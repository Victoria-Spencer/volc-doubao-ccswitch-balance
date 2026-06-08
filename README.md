# Volc Doubao CC Balance Monitor Tool

火山引擎豆包 CC 余额监控工具

---

## 📌 项目简介

这是一款专为**火山引擎豆包API**设计的余额监控工具，由Java后端服务、Python图形化配置界面和预打包可执行程序组成，无需复杂配置即可快速部署使用。

---

## ✨ 核心功能

- 豆包API余额实时查询与监控
- 服务进程自动重启与异常恢复
- 图形化配置界面，支持一键保存配置
- 系统托盘后台运行，不占用前台窗口
- 配置文件永久保存，重启不丢失

---

## 📂 项目目录结构

```plaintext
volc-doubao-ccswitch-balance/
├── .git/                 # Git版本控制目录
├── builder/              # Python打包工具目录
│   ├── volc_balance_tool.py      # 图形化配置脚本
│   └── volc-balance-service.jar  # Java服务端Jar包
├── dist/                 # 预打包成品目录
│   └── VolcBalanceTool.exe    # 可执行程序（内置Jar包）
├── volc-balance-service/ # Java后端源码目录
│   ├── src/              # Java业务源码
│   ├── pom.xml           # Maven配置文件
│   └── target/           # 编译输出目录
└── README.md             # 项目说明文档


```

---

## 🛠️ 模块说明

### 1. Java 后端服务 (`volc-balance-service/`)

- 核心业务逻辑实现，负责火山引擎API请求、余额查询功能
- 基于Spring Boot开发，支持自定义端口和配置文件
- 提供RESTful接口供CC-Switch调用获取余额数据
- 可独立编译为Jar包运行，无需额外依赖

### 2. Python 图形化配置工具 (`builder/volc_balance_tool.py`)

- 基于Tkinter开发的跨平台可视化配置界面
- 支持端口、AK/SK、检查间隔、CC进程名等参数配置
- 一键保存配置，自动生成`application.yml`与`cc-switch-balance-config.js`
- 系统托盘后台运行，窗口关闭后不退出程序
- 内置Jar包自动加载逻辑，优先使用同目录外置Jar包

### 3. 预打包可执行程序 (`dist/VolcBalanceService.exe`)

- 已内置Java服务Jar包，开箱即用
- 无需安装Python环境和任何依赖
- 配置文件自动保存到exe所在目录，永久生效
- 支持外置Jar包替换，无需重新打包程序

---

## 🚀 使用说明

### 方式一：直接运行预打包程序（推荐普通用户）

1.  下载 `dist/VolcBalanceService.exe` 到本地任意目录
2.  双击运行程序，程序会自动加载内置的Java服务
3.  切换到 `Settings` 标签页，填写必要配置：
    - `CC-Switch Process`：CC进程名（默认 `cc-switch.exe`，一般无需修改）
    - `Service Port`：本地服务监听端口（默认 `56790`，确保未被占用）
    - `Check Interval(s)`：服务状态检查间隔（默认 `2` 秒）
    - `VolcEngine Configuration`：填写火山引擎AK/SK与Region（默认 `cn-beijing`）
4.  点击 `Save Config` 保存配置，此时exe所在目录会自动生成两个配置文件：
    - `application.yml`：程序核心配置文件
    - `cc-switch-balance-config.js`：CC-Switch用量查询提取器代码
5.  **配置CC-Switch用量查询**：
    - 打开CC-Switch，进入「配置用量查询 - DouBaoSeed」页面
    - 开启「启用用量查询」开关，切换到「自定义」模板标签
    - 找到「提取器代码」输入框，将 `cc-switch-balance-config.js` 中的完整代码复制粘贴进去
    - 按需设置「自动查询间隔」，点击「保存配置」
6.  切换到 `Dashboard` 标签页，点击 `Start Monitor` 启动监控服务，状态会实时显示

### 方式二：开发/自定义使用（推荐开发者）

1.  **Java后端编译**：
    - 确保已安装JDK 21+和Maven
    - 进入 `volc-balance-service/` 目录，执行命令：
    ```bash
    mvn clean package -DskipTests
    ```
2.  **拷贝 Jar 包**：
    - 将编译完成的 `target/volc-balance-service.jar` 复制到 `builder/` 目录下
3.  **运行 Python 脚本调试**：
    - 确保已安装 Python 3.8+，执行依赖安装命令

    ```bash
    pip install pystray pillow pyyaml
    ```

    - 进入 `builder/` 目录，运行脚本：

    ```bash
    python volc_balance_tool.py
    ```

4.  **打包为 exe 可执行文件**：
    - 保持当前目录为 `builder/`，执行打包命令：

    ```bash
    pyinstaller --onefile --windowed --name VolcBalanceTool --add-data "volc-balance-service.jar;." volc_balance_tool.py
    ```

    - 打包完成后，可在 `builder/dist/` 目录获取生成的可执行程序
