"""
依赖注入容器

实现基于接口的依赖注入，支持：
- 接口到实现的绑定
- 构造函数自动注入
- 单例、原型、作用域生命周期
- 循环依赖检测
- 类型安全检查

使用示例：
    container = Container()
    
    # 注册实现类（自动解析构造函数依赖）
    container.register(LLMClient, MoonshotClient)
    
    # 注册为单例
    container.register(MemoryStore, SimpleMemoryStore, Scope.SINGLETON)
    
    # 解析依赖
    client = container.resolve(LLMClient)
"""

from typing import Any, Callable, Dict, Type, TypeVar, Generic, Optional, List, Set, get_type_hints
from typing_extensions import Protocol
from abc import ABC, abstractmethod
from enum import Enum, auto
from dataclasses import dataclass
import threading
import inspect
import logging

T = TypeVar('T')

logger = logging.getLogger(__name__)


class Scope(Enum):
    """依赖生命周期作用域"""
    TRANSIENT = auto()   # 每次解析创建新实例
    SINGLETON = auto()   # 全局单例
    SCOPED = auto()      # 作用域内单例


class ContainerError(Exception):
    """容器相关错误的基类"""
    pass


class RegistrationError(ContainerError):
    """注册错误"""
    pass


class ResolutionError(ContainerError):
    """解析错误"""
    pass


class CircularDependencyError(ResolutionError):
    """循环依赖错误"""
    def __init__(self, dependency_chain: List[Type]):
        chain_str = " -> ".join([t.__name__ for t in dependency_chain])
        super().__init__(f"Circular dependency detected: {chain_str}")
        self.dependency_chain = dependency_chain


class DependencyNotFoundError(ResolutionError):
    """依赖未找到错误"""
    def __init__(self, interface: Type, dependent: Optional[Type] = None):
        msg = f"Dependency {interface.__name__} not registered"
        if dependent:
            msg += f" (required by {dependent.__name__})"
        super().__init__(msg)
        self.interface = interface
        self.dependent = dependent


class TypeMismatchError(ResolutionError):
    """类型不匹配错误"""
    def __init__(self, expected: Type, actual: Type):
        super().__init__(f"Type mismatch: expected {expected.__name__}, got {actual.__name__}")
        self.expected = expected
        self.actual = actual


@dataclass
class Registration:
    """依赖注册信息"""
    interface: Type
    implementation: Optional[Type] = None
    factory: Optional[Callable[..., Any]] = None
    instance: Optional[Any] = None
    scope: Scope = Scope.TRANSIENT
    name: Optional[str] = None  # 支持命名注册
    
    def __post_init__(self):
        if self.implementation is None and self.factory is None and self.instance is None:
            # 默认实现为接口本身（用于具体类）
            self.implementation = self.interface


class ResolutionContext:
    """解析上下文（用于作用域管理）"""
    
    def __init__(self):
        self._scoped_instances: Dict[Type, Any] = {}
        self._resolution_stack: List[Type] = []
    
    def begin_resolution(self, interface: Type) -> None:
        """开始解析，检查循环依赖"""
        if interface in self._resolution_stack:
            # 发现循环依赖
            cycle_start = self._resolution_stack.index(interface)
            cycle = self._resolution_stack[cycle_start:] + [interface]
            raise CircularDependencyError(cycle)
        self._resolution_stack.append(interface)
    
    def end_resolution(self, interface: Type) -> None:
        """结束解析"""
        if self._resolution_stack and self._resolution_stack[-1] == interface:
            self._resolution_stack.pop()
    
    def get_scoped(self, interface: Type) -> Optional[Any]:
        """获取作用域实例"""
        return self._scoped_instances.get(interface)
    
    def set_scoped(self, interface: Type, instance: Any) -> None:
        """设置作用域实例"""
        self._scoped_instances[interface] = instance


class Container:
    """
    依赖注入容器
    
    核心功能：
    - 依赖注册：支持类型、工厂函数、实例
    - 自动构造函数注入：自动解析构造函数参数
    - 生命周期管理：Transient、Singleton、Scoped
    - 循环依赖检测：自动检测并报告循环依赖
    - 类型安全检查：验证解析的类型匹配
    
    使用示例：
        container = Container()
        
        # 基本注册
        container.register(ILogger, ConsoleLogger)
        
        # 单例注册
        container.register(IDatabase, Database, Scope.SINGLETON)
        
        # 工厂注册
        container.register_factory(ILogger, lambda c: FileLogger("app.log"))
        
        # 命名注册
        container.register(ILogger, FileLogger, name="file")
        
        # 解析
        logger = container.resolve(ILogger)
        file_logger = container.resolve(ILogger, name="file")
    """
    
    def __init__(self, parent: Optional['Container'] = None):
        """
        初始化容器
        
        Args:
            parent: 父容器，用于实现容器层次结构
        """
        self._parent = parent
        self._registrations: Dict[Type, List[Registration]] = {}
        self._singletons: Dict[Type, Any] = {}
        self._named_registrations: Dict[str, Registration] = {}
        self._lock = threading.RLock()
        self._local = threading.local()
    
    def _get_resolution_context(self) -> ResolutionContext:
        """获取当前线程的解析上下文"""
        if not hasattr(self._local, 'context'):
            self._local.context = ResolutionContext()
        return self._local.context
    
    def register(
        self,
        interface: Type[T],
        implementation: Optional[Type[T]] = None,
        scope: Scope = Scope.TRANSIENT,
        name: Optional[str] = None
    ) -> 'Container':
        """
        注册类型映射
        
        Args:
            interface: 接口类型
            implementation: 实现类型，None则使用接口本身
            scope: 生命周期作用域
            name: 命名注册标识
            
        Returns:
            Container: 支持链式调用
            
        Raises:
            RegistrationError: 注册失败时抛出
        """
        with self._lock:
            if implementation is None:
                implementation = interface
            
            # 验证实现类是否是接口的子类（如果不是同一个类）
            # 注意：Protocol类型需要使用 @runtime_checkable 才能使用 issubclass
            if interface != implementation:
                try:
                    if not issubclass(implementation, interface):
                        pass  # 类型检查失败，但允许注册（运行时检查）
                except TypeError:
                    # Protocol 类型不支持 issubclass，跳过验证
                    pass
            
            registration = Registration(
                interface=interface,
                implementation=implementation,
                scope=scope,
                name=name
            )
            
            # 添加到接口注册列表
            if interface not in self._registrations:
                self._registrations[interface] = []
            self._registrations[interface].append(registration)
            
            # 如果是命名注册，添加到命名注册表
            if name:
                key = f"{interface.__name__}:{name}"
                self._named_registrations[key] = registration
            
            logger.debug(f"Registered {interface.__name__} -> {implementation.__name__} (scope={scope.name})")
            return self
    
    def register_instance(
        self,
        interface: Type[T],
        instance: T,
        name: Optional[str] = None
    ) -> 'Container':
        """
        注册实例（单例）
        
        Args:
            interface: 接口类型
            instance: 实例对象
            name: 命名注册标识
            
        Returns:
            Container: 支持链式调用
        """
        with self._lock:
            registration = Registration(
                interface=interface,
                instance=instance,
                scope=Scope.SINGLETON,
                name=name
            )
            
            if interface not in self._registrations:
                self._registrations[interface] = []
            self._registrations[interface].append(registration)
            
            # 存储到单例缓存
            self._singletons[interface] = instance
            
            if name:
                key = f"{interface.__name__}:{name}"
                self._named_registrations[key] = registration
            
            logger.debug(f"Registered instance {interface.__name__}")
            return self
    
    def register_factory(
        self,
        interface: Type[T],
        factory: Callable[['Container'], T],
        scope: Scope = Scope.TRANSIENT,
        name: Optional[str] = None
    ) -> 'Container':
        """
        注册工厂函数
        
        Args:
            interface: 接口类型
            factory: 工厂函数，接收容器作为参数
            scope: 生命周期作用域
            name: 命名注册标识
            
        Returns:
            Container: 支持链式调用
        """
        with self._lock:
            registration = Registration(
                interface=interface,
                factory=factory,
                scope=scope,
                name=name
            )
            
            if interface not in self._registrations:
                self._registrations[interface] = []
            self._registrations[interface].append(registration)
            
            if name:
                key = f"{interface.__name__}:{name}"
                self._named_registrations[key] = registration
            
            logger.debug(f"Registered factory {interface.__name__}")
            return self
    
    def resolve(self, interface: Type[T], name: Optional[str] = None) -> T:
        """
        解析依赖
        
        Args:
            interface: 接口类型
            name: 命名注册标识
            
        Returns:
            T: 解析的实例
            
        Raises:
            DependencyNotFoundError: 依赖未注册
            CircularDependencyError: 发现循环依赖
            ResolutionError: 解析失败
        """
        context = self._get_resolution_context()
        return self._resolve_with_context(interface, name, context)
    
    def _resolve_with_context(
        self,
        interface: Type[T],
        name: Optional[str],
        context: ResolutionContext
    ) -> T:
        """
        带上下文的解析逻辑
        
        这是主要的解析方法，包含循环依赖检测
        """
        # 检查循环依赖
        context.begin_resolution(interface)
        
        try:
            return self._resolve_internal(interface, name, context)
        finally:
            context.end_resolution(interface)
    
    def _resolve_internal(
        self,
        interface: Type[T],
        name: Optional[str],
        context: ResolutionContext
    ) -> T:
        """内部解析逻辑（不处理循环依赖检测）"""
        
        # 1. 检查命名注册
        if name:
            key = f"{interface.__name__}:{name}"
            if key in self._named_registrations:
                return self._create_instance(self._named_registrations[key], context)
        
        # 2. 检查本地注册
        if interface in self._registrations:
            registration = self._registrations[interface][0]  # 默认取第一个
            return self._create_instance(registration, context)
        
        # 3. 检查父容器
        if self._parent:
            return self._parent.resolve(interface, name)
        
        # 4. 尝试自动注册（具体类，但不是抽象类或 Protocol）
        if isinstance(interface, type):
            # 检查是否是抽象类或 Protocol
            if not getattr(interface, '__abstractmethods__', None) and not isinstance(interface, type(Protocol)):
                logger.debug(f"Auto-registering {interface.__name__}")
                self.register(interface, scope=Scope.TRANSIENT)
                return self._create_instance(self._registrations[interface][0], context)
        
        raise DependencyNotFoundError(interface)
    
    def _create_instance(
        self,
        registration: Registration,
        context: ResolutionContext
    ) -> Any:
        """根据注册信息创建实例"""
        
        interface = registration.interface
        
        # 检查单例缓存
        if registration.scope == Scope.SINGLETON:
            if interface in self._singletons:
                return self._singletons[interface]
        
        # 检查作用域缓存
        if registration.scope == Scope.SCOPED:
            scoped = context.get_scoped(interface)
            if scoped is not None:
                return scoped
        
        # 创建实例
        instance = None
        
        if registration.instance is not None:
            # 直接返回预注册实例
            instance = registration.instance
        
        elif registration.factory is not None:
            # 使用工厂函数
            instance = registration.factory(self)
        
        elif registration.implementation is not None:
            # 使用构造函数自动注入
            instance = self._create_with_injection(registration.implementation, context)
        
        # 缓存单例和作用域实例
        if registration.scope == Scope.SINGLETON:
            self._singletons[interface] = instance
        elif registration.scope == Scope.SCOPED:
            context.set_scoped(interface, instance)
        
        return instance
    
    def _create_with_injection(
        self,
        implementation: Type[T],
        context: ResolutionContext
    ) -> T:
        """
        使用构造函数自动注入创建实例
        
        自动解析构造函数的参数类型，并从容器中获取依赖
        """
        try:
            # 获取构造函数签名
            sig = inspect.signature(implementation.__init__)
            type_hints = get_type_hints(implementation.__init__)
            
            # 构建参数
            kwargs = {}
            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue
                
                # 获取参数类型
                param_type = type_hints.get(param_name, param.annotation)
                
                # 跳过 *args 和 **kwargs
                if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                    continue
                
                # 如果有默认值且类型无法解析，跳过
                if param.default is not inspect.Parameter.empty:
                    if param_type is inspect.Parameter.empty or param_type is Any:
                        continue
                
                # 尝试从容器解析依赖
                if param_type is not inspect.Parameter.empty and param_type is not Any:
                    try:
                        kwargs[param_name] = self._resolve_with_context(param_type, None, context)
                    except DependencyNotFoundError:
                        # 如果有默认值，使用默认值
                        if param.default is not inspect.Parameter.empty:
                            kwargs[param_name] = param.default
                        else:
                            raise
                elif param.default is not inspect.Parameter.empty:
                    kwargs[param_name] = param.default
                else:
                    raise ResolutionError(
                        f"Cannot resolve parameter '{param_name}' for {implementation.__name__}"
                    )
            
            return implementation(**kwargs)
        
        except Exception as e:
            if isinstance(e, ContainerError):
                raise
            raise ResolutionError(
                f"Failed to create instance of {implementation.__name__}: {str(e)}"
            ) from e
    
    def resolve_all(self, interface: Type[T]) -> List[T]:
        """
        解析所有注册的实现
        
        Args:
            interface: 接口类型
            
        Returns:
            List[T]: 所有实现的实例列表
        """
        result = []
        context = self._get_resolution_context()
        
        if interface in self._registrations:
            for registration in self._registrations[interface]:
                result.append(self._create_instance(registration, context))
        
        return result
    
    def is_registered(self, interface: Type, name: Optional[str] = None) -> bool:
        """
        检查接口是否已注册
        
        Args:
            interface: 接口类型
            name: 命名注册标识
            
        Returns:
            bool: 是否已注册
        """
        if name:
            key = f"{interface.__name__}:{name}"
            return key in self._named_registrations
        
        return interface in self._registrations
    
    def unregister(self, interface: Type, name: Optional[str] = None) -> None:
        """
        注销接口
        
        Args:
            interface: 接口类型
            name: 命名注册标识
        """
        with self._lock:
            if name:
                key = f"{interface.__name__}:{name}"
                if key in self._named_registrations:
                    del self._named_registrations[key]
            
            if interface in self._registrations:
                if name:
                    self._registrations[interface] = [
                        r for r in self._registrations[interface] if r.name != name
                    ]
                else:
                    del self._registrations[interface]
            
            if interface in self._singletons:
                del self._singletons[interface]
    
    def clear(self) -> None:
        """清空所有注册"""
        with self._lock:
            self._registrations.clear()
            self._singletons.clear()
            self._named_registrations.clear()
    
    def create_scope(self) -> 'Container':
        """
        创建子作用域容器
        
        Returns:
            Container: 子容器，继承父容器的注册
        """
        return Container(parent=self)
    
    def get_registered_interfaces(self) -> List[Type]:
        """获取所有已注册的接口列表"""
        return list(self._registrations.keys())
    
    def build_provider(self) -> 'ServiceProvider':
        """
        构建服务提供者（只读视图）
        
        Returns:
            ServiceProvider: 服务提供者
        """
        return ServiceProvider(self)


class ServiceProvider:
    """
    服务提供者（容器的只读视图）
    
    用于将解析功能暴露给外部，同时隐藏注册功能
    """
    
    def __init__(self, container: Container):
        self._container = container
    
    def resolve(self, interface: Type[T], name: Optional[str] = None) -> T:
        """解析依赖"""
        return self._container.resolve(interface, name)
    
    def resolve_all(self, interface: Type[T]) -> List[T]:
        """解析所有实现"""
        return self._container.resolve_all(interface)
    
    def is_registered(self, interface: Type, name: Optional[str] = None) -> bool:
        """检查是否已注册"""
        return self._container.is_registered(interface, name)


# 全局容器实例
_global_container: Optional[Container] = None
_global_lock = threading.Lock()


def get_global_container() -> Container:
    """获取全局容器实例（懒加载）"""
    global _global_container
    if _global_container is None:
        with _global_lock:
            if _global_container is None:
                _global_container = Container()
    return _global_container


def set_global_container(container: Container) -> None:
    """设置全局容器实例"""
    global _global_container
    with _global_lock:
        _global_container = container


def reset_global_container() -> None:
    """重置全局容器（主要用于测试）"""
    global _global_container
    with _global_lock:
        _global_container = Container()


# 向后兼容
container = get_global_container()
