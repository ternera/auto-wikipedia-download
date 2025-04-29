#!/usr/bin/env python3

import os
import sys
import requests
import platform
import subprocess
import tempfile
import codecs
import threading
import queue
from tqdm.auto import tqdm

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def download_file(url, output_path, force_new=True):
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    
    file_size = 0
    headers = {}
    
    if os.path.exists(output_path) and not force_new:
        file_size = os.path.getsize(output_path)
        headers = {'Range': f'bytes={file_size}-'}
        print(f"Resuming download from {file_size} bytes")
    elif os.path.exists(output_path):
        os.remove(output_path)
    
    try:
        with requests.get(url, headers=headers, stream=True, timeout=30) as response:
            if file_size > 0 and response.status_code == 206:
                mode = 'ab'
            else:
                mode = 'wb'
                file_size = 0
            
            total_size = int(response.headers.get('content-length', 0)) + file_size
            
            progress_bar = tqdm(
                total=total_size,
                initial=file_size,
                unit='B',
                unit_scale=True,
                desc=os.path.basename(output_path),
                ascii=True if platform.system() == 'Windows' else False
            )
            
            with open(output_path, mode) as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        progress_bar.update(len(chunk))
            
            progress_bar.close()
            
    except requests.exceptions.RequestException as e:
        print(f"Error during download: {e}")
        sys.exit(1)

def setup_windows_task():
    task_template_path = os.path.join(SCRIPT_DIR, "windows_task.xml")
    if not os.path.exists(task_template_path):
        task_template_path = os.path.join(SCRIPT_DIR, "templates", "windows_task.xml")
    
    try:
        with open(task_template_path, 'r', encoding='utf-8') as f:
            task_xml = f.read()
            
        task_xml = task_xml.replace("{SCRIPT_DIR}", SCRIPT_DIR.replace('\\', '\\\\'))
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xml', mode='wb') as tmp:
            tmp_path = tmp.name
            tmp.write(codecs.BOM_UTF16_LE + task_xml.encode('utf-16-le'))
        
        result = subprocess.run(
            ['schtasks', '/create', '/tn', 'WikipediaWeeklyDownload', 
             '/xml', tmp_path, '/f'],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, result.args, 
                                                output=result.stdout, stderr=result.stderr)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'tmp_path' in locals():
            try:
                os.unlink(tmp_path)
            except:
                pass

def setup_macos_launchd():
    plist_template_path = os.path.join(SCRIPT_DIR, "com.user.wikipedia.download.plist")
    if not os.path.exists(plist_template_path):
        plist_template_path = os.path.join(SCRIPT_DIR, "templates", "com.user.wikipedia.download.plist")
    
    with open(plist_template_path, 'r') as f:
        plist_content = f.read()
    
    plist_content = plist_content.replace("{SCRIPT_DIR}", SCRIPT_DIR)
    plist_content = plist_content.replace("{PYTHON_PATH}", sys.executable)
    plist_content = plist_content.replace("{LOG_DIR}", os.path.expanduser("~/Library/Logs"))
    
    launch_agents_dir = os.path.expanduser("~/Library/LaunchAgents")
    os.makedirs(launch_agents_dir, exist_ok=True)
    
    plist_path = os.path.join(launch_agents_dir, "com.user.wikipedia.download.plist")
    with open(plist_path, 'w') as f:
        f.write(plist_content)
    
    try:
        subprocess.run(['launchctl', 'unload', plist_path], stderr=subprocess.DEVNULL, check=False)
        subprocess.run(['launchctl', 'load', plist_path], check=True)
    except Exception as e:
        print(f"Error: {e}")

def setup_linux_cron():
    cron_template_path = os.path.join(SCRIPT_DIR, "linux_cron")
    if not os.path.exists(cron_template_path):
        cron_template_path = os.path.join(SCRIPT_DIR, "templates", "linux_cron")
    
    try:
        with open(cron_template_path, 'r') as f:
            cron_template = f.read()
        
        log_dir = os.path.expanduser("~/logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "wikipedia-download.log")
        
        cron_cmd = cron_template.replace("{SCRIPT_DIR}", SCRIPT_DIR)
        cron_cmd = cron_cmd.replace("{PYTHON_PATH}", sys.executable)
        cron_cmd = cron_cmd.replace("{SCRIPT_NAME}", os.path.basename(__file__))
        cron_cmd = cron_cmd.replace("{LOG_FILE}", log_file)
        
        existing_crontab = subprocess.run(
            ['crontab', '-l'], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.DEVNULL,
            text=True,
            check=False
        ).stdout
        
        if os.path.basename(__file__) in existing_crontab:
            return
        
        new_crontab = existing_crontab + cron_cmd + "\n"
        
        with tempfile.NamedTemporaryFile(delete=False, mode='w') as tmp:
            tmp_path = tmp.name
            tmp.write(new_crontab)
        
        subprocess.run(['crontab', tmp_path], check=True)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'tmp_path' in locals():
            try:
                os.unlink(tmp_path)
            except:
                pass

def setup_scheduler():
    system = platform.system()
    
    try:
        if system == 'Windows':
            setup_windows_task()
        elif system == 'Darwin':
            setup_macos_launchd()
        elif system == 'Linux':
            setup_linux_cron()
    except Exception:
        pass
    
def input_with_timeout(prompt, timeout=10):
    print(prompt, end='', flush=True)
    user_input = queue.Queue()
    
    def get_input():
        try:
            user_input.put(input())
        except:
            user_input.put(None)
    
    input_thread = threading.Thread(target=get_input)
    input_thread.daemon = True
    input_thread.start()
    
    try:
        return user_input.get(timeout=timeout)
    except queue.Empty:
        return 'n'

def main():
    url = "https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles.xml.bz2"
    output_path = os.path.join(SCRIPT_DIR, "enwiki-latest-pages-articles.xml.bz2")
    
    setup_sched = input_with_timeout("Set up automatic weekly downloads? (y/n, 10s timeout): ")
    if setup_sched and setup_sched.lower() == 'y':
        setup_scheduler()
    
    download_file(url, output_path, force_new=True)

if __name__ == "__main__":
    try:
        from tqdm.auto import tqdm
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "tqdm"])
    
    main()
