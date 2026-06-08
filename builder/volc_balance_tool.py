import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import subprocess
import sys
import threading
import time
import yaml
import pystray
from PIL import Image, ImageDraw
import shutil
import requests 
from datetime import datetime 

# ===================== 获取资源文件路径（适配打包后环境） =====================
def resource_path(relative_path):
    """获取内嵌资源路径"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ===================== 获取程序（exe/脚本）所在目录 =====================
def get_exe_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

# ===================== 日志记录函数 =====================
def write_log(message):
    """写入运行日志到service.log"""
    exe_dir = get_exe_dir()
    log_path = os.path.join(exe_dir, "service.log")
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{time_str}] {message}\n"
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(log_msg)
    except:
        pass

# ===================== 核心：自动释放内嵌Jar到exe同级目录 =====================
def auto_extract_jar():
    exe_dir = get_exe_dir()
    target_jar = os.path.join(exe_dir, "volc-balance-service.jar")
    
    # 如果exe目录已有jar，直接跳过
    if os.path.exists(target_jar):
        return target_jar
    
    # 没有则从内嵌资源复制出来
    try:
        inner_jar = resource_path("volc-balance-service.jar")
        shutil.copy2(inner_jar, target_jar)
        print(f"Jar包已自动释放到：{target_jar}")
        write_log(f"Jar包已自动释放到：{target_jar}")
    except Exception as e:
        print(f"释放Jar失败：{str(e)}")
        write_log(f"释放Jar失败：{str(e)}")
    return target_jar

class VolcBalanceConfigTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Volc-Balance-Service Config Tool")
        self.root.geometry("650x500")
        self.root.resizable(False, False)

        # ===================== 自动释放Jar包 =====================
        self.exe_dir = get_exe_dir()
        # 自动释放内嵌jar到exe同级目录
        self.jar_path = tk.StringVar(value=auto_extract_jar())

        # 其他配置变量
        self.cc_process = tk.StringVar(value="cc-switch.exe")
        self.port = tk.StringVar(value="56790")
        self.check_interval = tk.StringVar(value="30")
        self.access_key = tk.StringVar()
        self.secret_key = tk.StringVar()
        self.region = tk.StringVar(value="cn-beijing")

        # 守护进程控制
        self.monitor_running = False
        self.monitor_thread = None
        self.java_process = None
        self.status_var = tk.StringVar(value="✅ Status: Stopped")

        # 内嵌 CC-Switch JS 配置模板（无注释）
        self.JS_TEMPLATE = '''({
    request: {
        url: "http://localhost:{{PORT}}/api/volc/balance",
        method: "GET"
    },
    extractor: function(response) {
        return { remaining: response.remaining, unit: response.unit };
    }
})'''

        # 系统托盘
        self.tray_icon = None
        self.tray_thread = None

        # 界面
        self.create_notebook_ui()
        self.load_config_from_yml()

        self.root.protocol("WM_DELETE_WINDOW", self.hide_to_tray)
        self.create_tray_icon()

    # ===================== 界面代码 =====================
    def create_notebook_ui(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.dashboard_frame = ttk.Frame(notebook)
        notebook.add(self.dashboard_frame, text="Dashboard")
        self.create_dashboard_ui()

        self.settings_frame = ttk.Frame(notebook)
        notebook.add(self.settings_frame, text="Settings")
        self.create_settings_ui()

    def create_dashboard_ui(self):
        main = ttk.Frame(self.dashboard_frame, padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="Service Monitor Panel", font=("Arial", 16, "bold")).pack(pady=10)
        
        status_group = ttk.LabelFrame(main, text="Service Status", padding=15)
        status_group.pack(fill=tk.X, pady=10)
        ttk.Label(status_group, textvariable=self.status_var, font=("Arial", 12)).pack(anchor=tk.W)

        info_group = ttk.LabelFrame(main, text="Current Config", padding=15)
        info_group.pack(fill=tk.X, pady=10)
        self.port_label = ttk.Label(info_group, text=f"Port: {self.port.get()} | Process: {self.cc_process.get()}")
        self.port_label.pack(anchor=tk.W, pady=2)

        btn_group = ttk.Frame(main)
        btn_group.pack(pady=20)
        self.toggle_btn = ttk.Button(btn_group, text="Start Monitor", command=self.toggle_monitor, width=15)
        self.toggle_btn.grid(row=0, column=0, padx=10)
        ttk.Button(btn_group, text="Exit", command=self.on_exit, width=15).grid(row=0, column=1, padx=10)

        self.update_config_summary()

    def create_settings_ui(self):
        main = ttk.Frame(self.settings_frame, padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        jar_frame = ttk.LabelFrame(main, text="Basic Configuration", padding=10)
        jar_frame.pack(fill=tk.X, pady=8)
        jar_frame.columnconfigure(1, weight=1)

        ttk.Label(jar_frame, text="CC-Switch Process:").grid(row=0, column=0, sticky=tk.W, pady=3)
        ttk.Entry(jar_frame, textvariable=self.cc_process).grid(row=0, column=1, padx=5, sticky=tk.EW)

        ttk.Label(jar_frame, text="Service Port:").grid(row=1, column=0, sticky=tk.W, pady=3)
        ttk.Entry(jar_frame, textvariable=self.port).grid(row=1, column=1, padx=5, sticky=tk.EW)

        ttk.Label(jar_frame, text="Check Interval(s):").grid(row=2, column=0, sticky=tk.W, pady=3)
        ttk.Entry(jar_frame, textvariable=self.check_interval).grid(row=2, column=1, padx=5, sticky=tk.EW)

        volc_frame = ttk.LabelFrame(main, text="VolcEngine Configuration", padding=10)
        volc_frame.pack(fill=tk.X, pady=8)
        volc_frame.columnconfigure(1, weight=1)

        ttk.Label(volc_frame, text="Access Key:").grid(row=0, column=0, sticky=tk.W, pady=3)
        self.ak_entry = ttk.Entry(volc_frame, textvariable=self.access_key, show="*")
        self.ak_entry.grid(row=0, column=1, padx=5, sticky=tk.EW)
        tk.Button(
            volc_frame, text="👁️", command=lambda: self.toggle_pwd(self.ak_entry),
            relief=tk.FLAT, bd=0, highlightthickness=0, font=("Arial", 11),
            padx=4, pady=2, bg="#f0f0f0", fg="black", width=7
        ).grid(row=0, column=2, padx=2, sticky="ns")

        ttk.Label(volc_frame, text="Secret Key:").grid(row=1, column=0, sticky=tk.W, pady=3)
        self.sk_entry = ttk.Entry(volc_frame, textvariable=self.secret_key, show="*")
        self.sk_entry.grid(row=1, column=1, padx=5, sticky=tk.EW)
        tk.Button(
            volc_frame, text="👁️", command=lambda: self.toggle_pwd(self.sk_entry),
            relief=tk.FLAT, bd=0, highlightthickness=0, font=("Arial", 11),
            padx=4, pady=2, bg="#f0f0f0", fg="black", width=7
        ).grid(row=1, column=2, padx=2, sticky="ns")

        ttk.Label(volc_frame, text="Region:").grid(row=2, column=0, sticky=tk.W, pady=3)
        ttk.Entry(volc_frame, textvariable=self.region).grid(row=2, column=1, padx=5, sticky=tk.EW)
        ttk.Frame(volc_frame, width=80).grid(row=2, column=2, padx=2, sticky="ns")

        ttk.Button(main, text="Save Config", command=self.save_config_to_yml).pack(pady=15)

    def toggle_pwd(self, entry):
        entry.config(show="" if entry.cget("show") == "*" else "*")

    def update_config_summary(self):
        self.port_label.config(text=f"Port: {self.port.get()} | Process: {self.cc_process.get()}")
        self.root.after(1000, self.update_config_summary)

    def validate_input(self):
        if not os.path.exists(self.jar_path.get()):
            messagebox.showerror("Error", "Jar文件释放失败！")
            write_log("错误：Jar文件释放失败")
            return False
        if not self.port.get().isdigit() or not self.check_interval.get().isdigit():
            messagebox.showerror("Error", "Port/Interval must be numbers!")
            write_log("错误：端口/检查间隔必须为数字")
            return False
        if not all([self.access_key.get(), self.secret_key.get()]):
            messagebox.showerror("Error", "Please enter VolcEngine AK/SK!")
            write_log("错误：未填写AK/SK")
            return False
        return True

    def create_tray_icon(self):
        image = Image.new('RGB', (64, 64), color='#4A90E2')
        draw = ImageDraw.Draw(image)
        draw.ellipse([16,16,48,48], fill='white')
        
        menu = (
            pystray.MenuItem("Show Window", self.show_window, default=True), 
            pystray.MenuItem("Exit", self.quit_app)
        )
        
        self.tray_icon = pystray.Icon("VolcBalanceTool", image, "Volc-Balance-Service", menu)
        self.tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        self.tray_thread.start()

    def hide_to_tray(self):
        self.root.withdraw()

    def show_window(self, icon=None, item=None):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def quit_app(self, icon=None, item=None):
        self.on_exit()
        self.tray_icon.stop()
        self.root.quit()

    def is_port_occupied(self, port):
        try:
            # 只匹配 LISTENING 状态的端口，忽略 TIME_WAIT/ESTABLISHED 等连接状态
            cmd = f'netstat -ano | findstr /r /c:":{port}.*LISTENING"'
            result = subprocess.run(
                cmd, 
                creationflags=subprocess.CREATE_NO_WINDOW, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                shell=True
            )
            # 只有找到 LISTENING 状态的端口，才返回 True（被占用）
            return len(result.stdout.strip()) > 0
        except:
            return False

    def generate_cc_js_file(self):
        js_path = os.path.join(self.exe_dir, "cc-switch-balance-config.js")
        js_content = self.JS_TEMPLATE.replace("{{PORT}}", self.port.get())
        with open(js_path, "w", encoding="utf-8") as f:
            f.write(js_content)
        return js_path

    def get_yml_path(self):
        return os.path.join(self.exe_dir, "application.yml")

    # ===================== 自动清除AK/SK空格/换行 + 日志 =====================
    def save_config_to_yml(self):
        if not self.validate_input():
            return
        yml_path = self.get_yml_path()
        
        # 核心：自动去除密钥中的换行符、空格、首尾空白
        ak_clean = self.access_key.get().strip().replace("\n", "").replace(" ", "")
        sk_clean = self.secret_key.get().strip().replace("\n", "").replace(" ", "")
        
        config = {
            "server": {"port": int(self.port.get())},
            "volcengine": {"access-key": ak_clean, "secret-key": sk_clean, "region": self.region.get()},
            "monitor": {"jar_path": self.jar_path.get(), "cc_process": self.cc_process.get(), "check_interval": int(self.check_interval.get())}
        }
        with open(yml_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, sort_keys=False)
        self.generate_cc_js_file()
        messagebox.showinfo("Success", "配置保存成功！\n已自动清理密钥中的空格/换行")
        write_log("配置已保存，AK/SK已自动清理空白字符")

    # ===================== 修改：加载配置时也清理密钥 =====================
    def load_config_from_yml(self):
        try:
            yml_path = self.get_yml_path()
            if not os.path.exists(yml_path):
                return
            with open(yml_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            
            # 加载时也清理空白字符
            ak_clean = config["volcengine"]["access-key"].strip().replace("\n", "").replace(" ", "")
            sk_clean = config["volcengine"]["secret-key"].strip().replace("\n", "").replace(" ", "")
            
            self.port.set(str(config["server"]["port"]))
            self.access_key.set(ak_clean)
            self.secret_key.set(sk_clean)
            self.region.set(config["volcengine"]["region"])
            self.cc_process.set(config["monitor"]["cc_process"])
            self.check_interval.set(str(config["monitor"]["check_interval"]))
            write_log("成功加载配置文件")
        except Exception as e:
            write_log(f"加载配置失败：{str(e)}")
            pass

    # =====================删除java_error.log，仅保留java_output.log =====================
    def start_java_service(self):
        if self.java_process and self.java_process.poll() is None:
            return
        yml_path = self.get_yml_path()
        
        java_cmd = [
            "javaw", "-jar", self.jar_path.get(),
            f"--spring.config.location={yml_path}",
            f"--server.port={self.port.get()}"
        ]
        
        try:
            # 仅保留Java正常输出日志，删除错误日志
            stdout_log = open(os.path.join(self.exe_dir, "java_output.log"), "w", encoding="utf-8")
            
            self.java_process = subprocess.Popen(
                java_cmd, cwd=self.exe_dir,
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=stdout_log, stderr=subprocess.DEVNULL, text=True
            )
            self.status_var.set("🟢 Status: Java Service Started")
            write_log(f"Java服务已启动，端口：{self.port.get()}")
        except Exception as e:
            messagebox.showerror("Java Start Error", str(e))
            write_log(f"Java服务启动失败：{str(e)}")

    # ===================== 调用Java内置优雅关闭接口 =====================
    def stop_java_service(self):
        try:
            # 调用你Java代码里的 /shutdown 优雅关闭接口
            port = self.port.get()
            # 发送GET请求关闭服务（你Java里是GetMapping）
            requests.get(f"http://127.0.0.1:{port}/shutdown", timeout=3)
            # 等待服务正常退出释放端口
            time.sleep(1)
            write_log("Java服务已优雅关闭")
        except Exception:
            # 服务未启动/已关闭，忽略异常
            write_log("Java服务关闭失败（未运行）")
            pass

    def is_process_running(self, process_name):
        try:
            result = subprocess.run(f'tasklist /fi "IMAGENAME eq {process_name}"', creationflags=subprocess.CREATE_NO_WINDOW, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            output = result.stdout.decode('gbk', errors='ignore').lower()
            return process_name.lower() in output
        except:
            return False

    def is_port_listening(self, port):
        try:
            # 用正则匹配，不管端口和 LISTENING 之间有多少空格，都能匹配到
            cmd = f'netstat -ano | findstr /r /c:":{port}.*LISTENING"'
            result = subprocess.run(
                cmd, 
                creationflags=subprocess.CREATE_NO_WINDOW, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                shell=True
            )
            return len(result.stdout.strip()) > 0
        except:
            return False

    def monitor_loop(self):
        while self.monitor_running:
            cc_running = self.is_process_running(self.cc_process.get())
            if not cc_running:
                self.stop_java_service()
                self.root.after(0, lambda: self.status_var.set("✅ Status: Stopped (CC closed)"))
                write_log("CC进程已关闭，自动停止Java服务")
                time.sleep(1)
                continue
            if not self.is_port_listening(self.port.get()):
                self.start_java_service()
                write_log("检测到Java服务异常，自动重启")
            self.root.after(0, lambda: self.status_var.set("🟢 Status: Running"))
            time.sleep(int(self.check_interval.get()))

    def toggle_monitor(self):
        if not self.monitor_running:
            self.start_monitor()
        else:
            self.stop_monitor()

    def start_monitor(self):
        if not self.validate_input():
            return
        if self.is_port_occupied(self.port.get()):
            messagebox.showerror("Error", f"Port {self.port.get()} 被占用！")
            write_log(f"错误：端口{self.port.get()}被占用")
            return
        self.monitor_running = True
        self.toggle_btn.config(text="Stop Monitor")
        self.start_java_service()
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
        write_log("监控服务已启动")

    def stop_monitor(self):
        self.monitor_running = False
        self.stop_java_service()
        self.toggle_btn.config(text="Start Monitor")
        self.status_var.set("✅ Status: Stopped")
        write_log("监控服务已停止")

    def on_exit(self):
        self.stop_monitor()
        write_log("程序退出")
        self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = VolcBalanceConfigTool(root)
    root.mainloop()