"""测试生成任务"""
import asyncio
import logging
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_generation():
    from api.routes.generation import _run_generation_task, _tasks
    from api.dependencies import GenerationState
    from pydantic import BaseModel
    from typing import Optional
    
    class TestRequest(BaseModel):
        theme: str = "测试主题"
        style: str = "novel"
        total_words: int = 1000
        character_count: int = 2
        genre: str = "sci_fi"
        temperature: float = 0.7
        max_tokens: int = 1024
    
    # 初始化任务
    task_id = "test_123"
    _tasks[task_id] = {
        "id": task_id,
        "status": "pending",
        "request": {},
        "created_at": datetime.now().isoformat(),
        "result": None,
    }
    
    state = GenerationState()
    request = TestRequest()
    
    print(f"Starting test at {datetime.now()}")
    print(f"Output directory: {os.path.abspath('./output')}")
    
    try:
        await _run_generation_task(task_id, request, state)
        print(f"Task completed: {task_id}")
        print(f"Final status: {_tasks[task_id].get('status')}")
        
        # 检查 output 目录
        output_dir = "./output"
        if os.path.exists(output_dir):
            files = os.listdir(output_dir)
            print(f"Files in output directory: {files}")
            
            # 找到最新的文件
            txt_files = [f for f in files if f.endswith('.txt')]
            if txt_files:
                txt_files.sort(key=lambda x: os.path.getmtime(os.path.join(output_dir, x)), reverse=True)
                latest_file = txt_files[0]
                latest_path = os.path.join(output_dir, latest_file)
                file_size = os.path.getsize(latest_path)
                print(f"Latest file: {latest_file} ({file_size} bytes)")
        else:
            print("Output directory does not exist!")
            
    except Exception as e:
        logger.exception("Generation failed")
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_generation())
