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

# ===================== 获取资源文件路径（适配打包后环境） =====================
def resource_path(relative_path):
    """获取资源文件的绝对路径，支持PyInstaller打包后运行"""
    try:
        # 打包后，资源文件会被解压到sys._MEIPASS目录
        base_path = sys._MEIPASS
    except Exception:
        # 开发环境下，使用当前目录
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class VolcBalanceConfigTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Volc-Balance-Service Config Tool")
        self.root.geometry("650x500")
        self.root.resizable(False, False)

        # ===================== Jar包自动加载逻辑 =====================
        # 1. 优先使用同目录下的jar包（用户可自行替换）
        self.default_jar_path = os.path.join(os.path.abspath("."), "volc-balance-service.jar")
        if os.path.exists(self.default_jar_path):
            jar_path = self.default_jar_path
        else:
            # 2. 同目录无jar包时，使用内置打包的jar包
            jar_path = resource_path("volc-balance-service.jar")
        self.jar_path = tk.StringVar(value=jar_path)

        # 其他配置变量
        self.cc_process = tk.StringVar(value="cc-switch.exe")
        self.port = tk.StringVar(value="56790")
        self.check_interval = tk.StringVar(value="2")
        self.access_key = tk.StringVar()
        self.secret_key = tk.StringVar()
        self.region = tk.StringVar(value="cn-beijing")

        # 守护进程控制
        self.monitor_running = False
        self.monitor_thread = None
        self.java_process = None
        self.status_var = tk.StringVar(value="✅ Status: Stopped")

        # 内嵌 CC-Switch JS 配置模板
        self.JS_TEMPLATE = '''({
  // 请求配置
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

        # 界面：双标签页（主控面板 + 设置页）
        self.create_notebook_ui()
        self.load_config_from_yml()

        # 窗口关闭最小化到托盘
        self.root.protocol("WM_DELETE_WINDOW", self.hide_to_tray)
        self.create_tray_icon()

    # ===================== 核心：双标签页界面 =====================
    def create_notebook_ui(self):
        # 创建标签页控件
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 1. 主控面板（主页面）
        self.dashboard_frame = ttk.Frame(notebook)
        notebook.add(self.dashboard_frame, text="Dashboard")
        self.create_dashboard_ui()

        # 2. 配置设置页（编辑页）
        self.settings_frame = ttk.Frame(notebook)
        notebook.add(self.settings_frame, text="Settings")
        self.create_settings_ui()

    # ===================== Dashboard界面 =====================
    def create_dashboard_ui(self):
        main = ttk.Frame(self.dashboard_frame, padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        # 标题
        ttk.Label(main, text="Service Monitor Panel", font=("Arial", 16, "bold")).pack(pady=10)
        
        # 服务状态
        status_group = ttk.LabelFrame(main, text="Service Status", padding=15)
        status_group.pack(fill=tk.X, pady=10)
        ttk.Label(status_group, textvariable=self.status_var, font=("Arial", 12, "bold")).pack(anchor=tk.W)

        # 核心配置摘要（仅保留Port和Process）
        info_group = ttk.LabelFrame(main, text="Current Config", padding=15)
        info_group.pack(fill=tk.X, pady=10)
        self.port_label = ttk.Label(info_group, text=f"Port: {self.port.get()} | Process: {self.cc_process.get()}")
        self.port_label.pack(anchor=tk.W, pady=2)

        # 控制按钮
        btn_group = ttk.Frame(main)
        btn_group.pack(pady=20)
        self.toggle_btn = ttk.Button(btn_group, text="Start Monitor", command=self.toggle_monitor, width=15)
        self.toggle_btn.grid(row=0, column=0, padx=10)
        ttk.Button(btn_group, text="Exit", command=self.on_exit, width=15).grid(row=0, column=1, padx=10)

        # 实时更新摘要
        self.update_config_summary()

    # ===================== Settings界面 =====================
    def create_settings_ui(self):
        main = ttk.Frame(self.settings_frame, padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        # 基础配置
        jar_frame = ttk.LabelFrame(main, text="Basic Configuration", padding=10)
        jar_frame.pack(fill=tk.X, pady=8)
        jar_frame.columnconfigure(1, weight=1)

        # 1. CC-Switch Process（row=0）
        ttk.Label(jar_frame, text="CC-Switch Process:").grid(row=0, column=0, sticky=tk.W, pady=3)
        ttk.Entry(jar_frame, textvariable=self.cc_process).grid(row=0, column=1, padx=5, sticky=tk.EW)

        # 2. Service Port（row=1）
        ttk.Label(jar_frame, text="Service Port:").grid(row=1, column=0, sticky=tk.W, pady=3)
        ttk.Entry(jar_frame, textvariable=self.port).grid(row=1, column=1, padx=5, sticky=tk.EW)

        # 3. Check Interval(s)（row=2）
        ttk.Label(jar_frame, text="Check Interval(s):").grid(row=2, column=0, sticky=tk.W, pady=3)
        ttk.Entry(jar_frame, textvariable=self.check_interval).grid(row=2, column=1, padx=5, sticky=tk.EW)

        # 火山引擎配置
        volc_frame = ttk.LabelFrame(main, text="VolcEngine Configuration", padding=10)
        volc_frame.pack(fill=tk.X, pady=8)
        volc_frame.columnconfigure(1, weight=1)

        # Access Key + 眼睛按钮
        ttk.Label(volc_frame, text="Access Key:").grid(row=0, column=0, sticky=tk.W, pady=3)
        self.ak_entry = ttk.Entry(volc_frame, textvariable=self.access_key, show="*")
        self.ak_entry.grid(row=0, column=1, padx=5, sticky=tk.EW)
        tk.Button(
            volc_frame,
            text="👁️",
            command=lambda: self.toggle_pwd(self.ak_entry),
            relief=tk.FLAT,
            bd=0,
            highlightthickness=0,
            font=("Arial", 11),
            padx=4,
            pady=2,
            bg="#f0f0f0",
            fg="black",
            width=7
        ).grid(row=0, column=2, padx=2, sticky="ns")

        # Secret Key + 眼睛按钮
        ttk.Label(volc_frame, text="Secret Key:").grid(row=1, column=0, sticky=tk.W, pady=3)
        self.sk_entry = ttk.Entry(volc_frame, textvariable=self.secret_key, show="*")
        self.sk_entry.grid(row=1, column=1, padx=5, sticky=tk.EW)
        tk.Button(
            volc_frame,
            text="👁️",
            command=lambda: self.toggle_pwd(self.sk_entry),
            relief=tk.FLAT,
            bd=0,
            highlightthickness=0,
            font=("Arial", 11),
            padx=4,
            pady=2,
            bg="#f0f0f0",
            fg="black",
            width=7
        ).grid(row=1, column=2, padx=2, sticky="ns")

        # Region
        ttk.Label(volc_frame, text="Region:").grid(row=2, column=0, sticky=tk.W, pady=3)
        ttk.Entry(volc_frame, textvariable=self.region).grid(row=2, column=1, padx=5, sticky=tk.EW)
        ttk.Frame(volc_frame, width=80).grid(row=2, column=2, padx=2, sticky="ns")

        # 保存按钮
        ttk.Button(main, text="Save Config", command=self.save_config_to_yml).pack(pady=15)

    # 眼睛按钮：切换明文/隐藏
    def toggle_pwd(self, entry):
        entry.config(show="" if entry.cget("show") == "*" else "*")

    # ===================== 更新摘要，仅更新Port和Process =====================
    def update_config_summary(self):
        self.port_label.config(text=f"Port: {self.port.get()} | Process: {self.cc_process.get()}")
        self.root.after(1000, self.update_config_summary)

    # ===================== 验证输入逻辑，适配自动加载的Jar包 =====================
    def validate_input(self):
        # 检查Jar包是否存在（自动加载的路径）
        if not self.jar_path.get() or not os.path.exists(self.jar_path.get()):
            messagebox.showerror("Error", "Jar file not found! Please ensure the jar file exists.")
            return False
        # 检查端口和间隔是否为数字
        if not self.port.get().isdigit() or not self.check_interval.get().isdigit():
            messagebox.showerror("Error", "Port/Interval must be numbers!")
            return False
        # 检查火山引擎配置
        if not all([self.access_key.get(), self.secret_key.get()]):
            messagebox.showerror("Error", "Please enter VolcEngine AK/SK!")
            return False
        return True

    # 系统托盘
    def create_tray_icon(self):
        image = Image.new('RGB', (64, 64), color='#4A90E2')
        draw = ImageDraw.Draw(image)
        draw.ellipse([16,16,48,48], fill='white')
        
        menu = (
            pystray.MenuItem(
                "Show Window", 
                self.show_window,
                default=True
            ), 
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

    # 端口占用检查
    def is_port_occupied(self, port):
        try:
            result = subprocess.run(f'netstat -ano | findstr ":{port}"', creationflags=subprocess.CREATE_NO_WINDOW, stdout=subprocess.PIPE, shell=True)
            return len(result.stdout.strip()) > 0
        except:
            return False

    # 生成CC-Switch配置文件
    def generate_cc_js_file(self):
        target_dir = os.path.dirname(self.jar_path.get())
        js_path = os.path.join(target_dir, "cc-switch-balance-config.js")
        js_content = self.JS_TEMPLATE.replace("{{PORT}}", self.port.get())
        with open(js_path, "w", encoding="utf-8") as f:
            f.write(js_content)
        return js_path

    # 获取配置文件路径
    def get_yml_path(self):
        if not self.jar_path.get():
            return None
        return os.path.join(os.path.dirname(self.jar_path.get()), "application.yml")

    # 保存配置到文件
    def save_config_to_yml(self):
        if not self.validate_input():
            return
        yml_path = self.get_yml_path()
        config = {
            "server": {"port": int(self.port.get())},
            "volcengine": {"access-key": self.access_key.get(), "secret-key": self.secret_key.get(), "region": self.region.get()},
            "monitor": {"jar_path": self.jar_path.get(), "cc_process": self.cc_process.get(), "check_interval": int(self.check_interval.get())}
        }
        with open(yml_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, sort_keys=False)
        self.generate_cc_js_file()
        messagebox.showinfo("Success", "Config saved successfully!")

    # ===================== 加载配置文件时，保留自动加载的Jar路径 =====================
    def load_config_from_yml(self):
        try:
            yml_path = os.path.join(os.getcwd(), "application.yml")
            if not os.path.exists(yml_path):
                return
            with open(yml_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            # 加载配置文件中的其他参数
            self.port.set(str(config["server"]["port"]))
            self.access_key.set(config["volcengine"]["access-key"])
            self.secret_key.set(config["volcengine"]["secret-key"])
            self.region.set(config["volcengine"]["region"])
            self.cc_process.set(config["monitor"]["cc_process"])
            self.check_interval.set(str(config["monitor"]["check_interval"]))
            
            # 配置文件中的Jar路径如果有效，才覆盖自动加载的路径
            jar_path_config = config["monitor"]["jar_path"]
            if os.path.exists(jar_path_config):
                self.jar_path.set(jar_path_config)
        except:
            pass

    # 启动Java服务
    def start_java_service(self):
        if self.java_process and self.java_process.poll() is None:
            return
        jar_dir = os.path.dirname(self.jar_path.get())
        try:
            self.java_process = subprocess.Popen(["javaw", "-jar", self.jar_path.get()], cwd=jar_dir, creationflags=subprocess.CREATE_NO_WINDOW, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.status_var.set("🟢 Status: Java Service Started")
        except Exception as e:
            messagebox.showerror("Java Start Error", str(e))

    # 停止Java服务
    def stop_java_service(self):
        try:
            subprocess.run(f'taskkill /F /IM javaw.exe', creationflags=subprocess.CREATE_NO_WINDOW, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.java_process = None
        except:
            pass

    # 检查进程是否运行
    def is_process_running(self, process_name):
        try:
            result = subprocess.run(f'tasklist /fi "IMAGENAME eq {process_name}"', creationflags=subprocess.CREATE_NO_WINDOW, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            output = result.stdout.decode('gbk', errors='ignore').lower()
            return process_name.lower() in output
        except:
            return False

    # 检查端口是否监听
    def is_port_listening(self, port):
        try:
            result = subprocess.run(f'netstat -ano | findstr ":{port} LISTENING"', creationflags=subprocess.CREATE_NO_WINDOW, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            return len(result.stdout.strip()) > 0
        except:
            return False

    # 守护进程循环
    def monitor_loop(self):
        while self.monitor_running:
            cc_running = self.is_process_running(self.cc_process.get())
            if not cc_running:
                self.stop_java_service()
                self.root.after(0, lambda: self.status_var.set("✅ Status: Stopped (CC closed)"))
                time.sleep(1)
                continue
            if not self.is_port_listening(self.port.get()):
                self.start_java_service()
            self.root.after(0, lambda: self.status_var.set("🟢 Status: Running"))
            time.sleep(int(self.check_interval.get()))

    # 切换监控状态
    def toggle_monitor(self):
        if not self.monitor_running:
            self.start_monitor()
        else:
            self.stop_monitor()

    # 启动监控
    def start_monitor(self):
        if not self.validate_input():
            return
        if self.is_port_occupied(self.port.get()):
            messagebox.showerror("Error", f"Port {self.port.get()} is occupied!")
            return
        self.monitor_running = True
        self.toggle_btn.config(text="Stop Monitor")
        self.start_java_service()
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()

    # 停止监控
    def stop_monitor(self):
        self.monitor_running = False
        self.stop_java_service()
        self.toggle_btn.config(text="Start Monitor")
        self.status_var.set("✅ Status: Stopped")

    # 退出程序
    def on_exit(self):
        self.stop_monitor()
        self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = VolcBalanceConfigTool(root)
    root.mainloop()