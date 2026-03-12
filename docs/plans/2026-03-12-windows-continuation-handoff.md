# Screen Human Lab Windows Continuation Handoff

- Handoff date: 2026-03-12
- Project root: `/Users/ljs/screen-human-lab`
- Current branch: `main`
- Current HEAD: `10cd590`
- Current state: working tree is **dirty** and contains both modified files and untracked files; this is **not** a clean committed checkpoint yet.
- Primary continuation target: a Windows machine with NVIDIA GPU, priority on **Windows-first runtime verification and continued development**.
- User preference summary:
  - Windows 优先
  - 先把非训练部分打稳
  - 目标显示和锁定更准
  - 高速晃动场景下要更稳
  - 先做 A 方案：**原生 Win32 分层窗口**
  - 先做 **ROI-only overlay**，不是全屏遮罩
  - 优先低延迟稳定显示
  - 点击穿透可以后做，不是第一优先级
  - 训练、RL、LLaVA、SAM、CLIP 等方案先做可行性评估，不要先落地成重训练流水线

---

## 1. 这份文档的用途

这份文档不是普通开发记录，而是为了在另一台 Windows 电脑上继续开发时实现“无缝续接”。

建议新的开发会话开始时，优先按下面顺序阅读：

1. 本文件：`docs/plans/2026-03-12-windows-continuation-handoff.md`
2. 设计文档：`docs/plans/2026-03-12-windows-stability-preview-design.md`
3. 实施文档：`docs/plans/2026-03-12-windows-stability-preview.md`
4. CLI 入口：`src/screen_human_lab/cli.py`
5. Windows overlay：`src/screen_human_lab/overlay/windows_overlay.py`
6. 稳定性核心运行时：`src/screen_human_lab/pipeline/gated_runtime.py`
7. 稳定预览会话：`src/screen_human_lab/pipeline/runtime.py`
8. 配置结构：`src/screen_human_lab/config.py`
9. 相关测试：`tests/test_preview_runtime.py`、`tests/test_windows_overlay.py`、`tests/test_cli_runtime.py`

---

## 2. 当前实际使用过的 skills

下面分成两类：

### 2.1 Codex / 本地开发流程 skills（已实际调用）

这些是当前开发过程中**明确使用过**的 Codex 本地技能：

1. `using-superpowers`
   - 用途：在每次任务开始前检查是否需要加载技能。
   - 作用：强制执行“先判断 skill，再行动”的流程。

2. `brainstorming`
   - 用途：在开始功能改动前先做方案讨论。
   - 作用：用于前面多轮关于 Windows 优先、非训练先行、A 方案 Win32 分层窗口、ROI-only overlay、低延迟优先的设计确认。

3. `writing-plans`
   - 用途：把较复杂的改动拆成分阶段执行计划。
   - 作用：用于梳理 Section1 到当前的 Windows 稳定性与 overlay 改造路线。

4. `test-driven-development`
   - 用途：在补功能时先加测试或同步补测试。
   - 作用：Phase 1 和 Phase 2 都采用“先有测试期望，再补实现，再跑验证”的方式推进。

5. `code-dev-standards`
   - 用途：保证代码和测试是一一对应的，行为变化必须有测试覆盖。
   - 作用：本次新增的 Windows 分支、稳定性模块、配置项和 overlay helper 都有对应测试。

6. `verification-before-completion`
   - 用途：在声称“完成/通过”前必须运行验证命令。
   - 作用：本次所有“已完成”判断都以真实测试输出为依据，而不是推测。

7. `project-profile`
   - 用途：整理项目元信息、环境、工具链、命令、迁移资料。
   - 作用：本文件本身就属于这一类交接/迁移档案。

### 2.2 用户提过、做过方案评估，但**尚未落代码**的模型/训练栈

这些是前面对可行性进行过讨论或方案评估的“模型/训练栈/研究方向”，**不是当前仓库里已经完成的代码集成**：

- `CLIP`
- `BLIP-2`
- `Segment Anything`
- `LLaVA`
- `trl-fine-tuning`
- `grpo-rl-training`
- `openrlhf`
- `pytorch-lightning`
- `ray-train`
- `mlflow`
- `weights-and-biases`

当前状态：**仅做过方向性评估与方案建议，没有在本仓库中形成训练流水线代码闭环。**

---

## 3. 当前已经完成的工作

下面按“从已有基础能力”到“本轮重点新增能力”来记录。

### 3.1 项目原有/已打通的核心实时能力

这些能力在本轮继续开发前已经存在或已经在前面阶段打通：

1. 居中方形 ROI 截图
   - 只对中间 ROI 做实时处理，而不是整屏检测。
   - 当前常用 ROI 是 `500x500`。

2. 叠层/预览式可视化
   - 原有 macOS overlay 路线仍保留。
   - 现在新增了 Windows 优先路线。

3. 右键门控检测
   - 只在按住鼠标右键时执行检测，降低无效计算。

4. `L` 键服务开关
   - 可临时禁用/恢复检测服务，同时保留 ROI 边框状态反馈。

5. 单目标锁定
   - 每次只锁一个目标，避免多目标抖动切换。

6. 丢失恢复策略
   - 锁定目标丢失时，并不是立即重检，而是允许一定的丢失帧数。
   - 当前默认：超过 `5 lost frames` 才退回重检测。

7. `dx/dy` 偏移读数
   - overlay 上可显示相对偏移量。

8. 光标跟随控制
   - 已具备基于当前目标与当前光标位置的线性跟随逻辑。
   - 相关参数：`overlay.cursor_follow_speed`、`overlay.cursor_follow_min_distance`。

9. 稳定/快速 两套跟踪预设
   - `stable`
   - `fast`
   - 主要体现在模板匹配阈值、搜索区域和预测增益的不同组合。

### 3.2 本轮完成的 Windows 优先基础改造（Section1 到当前）

这是本轮最核心的产出。

#### 3.2.1 Windows-first 后端选择与配置扩展

已完成：

- `src/screen_human_lab/config.py`
  - 扩展支持后端：`auto`、`cuda`、`mps`、`cpu`
  - 新增 `select_runtime_backend(...)`
  - `auto` 模式现在优先逻辑是：
    1. 如果 CUDA 可用，优先 `cuda`
    2. 如果是 macOS 且 MPS 可用，则 `mps`
    3. 否则 `cpu`

实际意义：

- 在你的 Windows + NVIDIA 机器上，`backend: auto` 会优先走 CUDA。
- 这正符合你“Windows 优先”的要求。

#### 3.2.2 新增稳定性参数结构

已完成：

- `src/screen_human_lab/config.py`
  - 新增 `StabilityConfig`
  - 当前参数包括：
    - `enabled`
    - `enable_global_motion`
    - `max_lost_frames`
    - `confidence_weight`
    - `iou_weight`
    - `distance_weight`
    - `size_weight`
    - `smoothing_factor`
    - `switch_margin`

实际意义：

- 目标锁定和恢复不再是单一硬编码逻辑，而是可以通过配置调参。
- 后续如果你要继续做“更稳、更少误切换、更少抖动”，这就是主要调参入口之一。

#### 3.2.3 CUDA 推理后端接入

已完成：

- `src/screen_human_lab/inference/torch_cuda.py`
  - 新增 `TorchCudaBackend`
- `src/screen_human_lab/inference/factory.py`
  - `build_backend(...)` 现在可以构造 CUDA backend

当前实现方式：

- 使用 `torch` + `ultralytics.YOLO`
- `device='cuda'`
- `classes=[0]`，即仅保留 person 类

实际意义：

- 对你的 `GTX 1650 Ti`，这是当前最现实、最直接的 Windows 优先方案。
- 非训练优化阶段，优先把这条 CUDA 路径稳定跑通，比先引入 RL 更有价值。

#### 3.2.4 全局运动估计

已完成：

- `src/screen_human_lab/pipeline/global_motion.py`
  - 新增 `GlobalMotionEstimator`
  - 使用 phase correlation 估计两帧间整体位移

实际意义：

- 当画面高速晃动时，不是完全依赖“目标自己移动”，而是先估计整幅 ROI 的全局平移。
- 这对你要求的“高速晃动下稳定性更好”是非常关键的基础能力。

#### 3.2.5 目标打分与单目标选择

已完成：

- `src/screen_human_lab/pipeline/target_scoring.py`
  - 新增多因子评分
  - 评分因素包括：
    - 置信度
    - 与预测框的 IoU
    - 与预测框的尺寸相似度
    - 与参考中心/预测位置的距离

实际意义：

- 目标选择不再只是“谁分数高就选谁”，而是把“时序一致性”和“空间连续性”考虑进来。
- 这能显著减少高速移动/遮挡时的误切换。

#### 3.2.6 目标状态平滑器

已完成：

- `src/screen_human_lab/pipeline/target_filter.py`
  - 新增 `TargetStateFilter`
  - 对 bbox 做指数平滑

实际意义：

- 检测框不会每帧生硬跳动。
- 对 overlay 稳定显示和后续 cursor follow 都有帮助。

#### 3.2.7 锁定状态机

已完成：

- `src/screen_human_lab/pipeline/lock_state.py`
  - 新增 `LockStateMachine`
  - 状态包括：
    - `idle`
    - `acquiring`
    - `locked`
    - `recovering`

实际意义：

- 让“锁定中 / 丢失恢复中 / 需要重新检测”变成显式状态，而不是散落在 if/else 里。
- 后续如果要调优稳定性或加入更复杂状态，会更容易扩展。

#### 3.2.8 模板跟踪增强

已完成：

- `src/screen_human_lab/tracking/template_match.py`
  - 增强了模板跟踪逻辑
  - 支持：
    - `prediction_gain`
    - 自适应搜索 padding
    - motion hint 参与预测

实际意义：

- 高速移动时，搜索窗口可以比原先更合理地放大。
- 这使得“检测之后继续跟踪”的连续性更强。

#### 3.2.9 稳定预览会话（Windows-first 非 overlay 路线）

已完成：

- `src/screen_human_lab/pipeline/runtime.py`
  - 新增 `StablePreviewSession`
- `src/screen_human_lab/pipeline/gated_runtime.py`
  - 新增稳定版 `GatedDetectionRuntime`

当前特征：

- 支持稳定性配置
- 支持全局运动补偿
- 支持单目标锁定
- 支持本地 ROI 坐标输出
- 结果中带：
  - `frame`
  - `state`
  - `motion`

实际意义：

- 这是 Windows 上最应该先跑通的路径。
- 它不依赖原生透明叠层窗口，调试成本更低，适合作为基准验证链路。

#### 3.2.10 Win32 ROI 原生分层叠层（A 方案）

已完成：

- `src/screen_human_lab/overlay/windows_overlay.py`
  - 已新增并补完
- `src/screen_human_lab/overlay/__init__.py`
  - 已导出 `windows_overlay`
- `src/screen_human_lab/cli.py`
  - 已新增 Windows overlay 路由分支

当前实现特征：

1. 平台限制
   - 仅 `win32` 平台可运行

2. 窗口模型
   - 使用原生 Win32 API
   - 使用 layered popup window
   - ROI-only window，不是全屏窗口
   - 置顶显示

3. 输入逻辑
   - 使用 `GetAsyncKeyState` 轮询：
     - 鼠标右键
     - `L` 键

4. 运行逻辑
   - 使用后台 worker 线程持续驱动 `GatedDetectionRuntime`
   - UI 刷新与检测线程解耦

5. 绘制内容
   - ROI 边框
   - 检测框
   - `dx/dy` 文本
   - 服务启停状态颜色反馈

6. 当前优先级选择
   - 先保证 ROI 范围内原生叠层显示稳定
   - 先不做 click-through 作为首要目标

实际意义：

- 这就是你确认的 **A 方案：原生 Win32 分层窗口**。
- 当前已经落到代码里，而不是停留在方案层。

### 3.3 已新增/更新的配置文件

当前新增的 Windows 相关配置：

1. `configs/realtime_win_cuda.yaml`
   - Windows 预览模式
   - `backend: auto`
   - `mode: preview`
   - 用于先验证稳定预览链路

2. `configs/realtime_win_cpu.yaml`
   - Windows CPU 预览模式
   - `backend: cpu`
   - `mode: preview`
   - 用于没有 CUDA 时的备选路线

3. `configs/realtime_win_overlay_cuda.yaml`
   - Windows 原生 ROI overlay 模式
   - `backend: auto`
   - `mode: overlay`
   - `infer_only_while_right_mouse_down: true`
   - 用于实际 Win32 overlay 路线

### 3.4 已新增/更新的测试

新增或强化的测试覆盖包括：

- `tests/test_cli_runtime.py`
- `tests/test_config.py`
- `tests/test_factory.py`
- `tests/test_gated_runtime.py`
- `tests/test_preview_runtime.py`
- `tests/test_project_files.py`
- `tests/test_template_tracker.py`
- `tests/test_global_motion.py`
- `tests/test_lock_state.py`
- `tests/test_target_filter.py`
- `tests/test_target_scoring.py`
- `tests/test_windows_overlay.py`

当前验证结果：

- 聚焦测试：`34 passed`
- 全量测试：`100 passed in 0.50s`

注意：

- 这些通过结果是在当前 macOS 开发环境上得到的。
- 其中 Win32 overlay 的“窗口实际显示”尚未在真实 Windows 机器上人工验证。
- 当前已经验证的是：Python 逻辑、坐标换算、CLI 路由、配置文件期望、运行时结构和相关单元测试。

---

## 4. 当前工作树状态（非常重要）

当前分支不是干净状态，很多修改**还没有 commit**。如果你要换到另一台 Windows 电脑继续开发，有两个推荐方式：

### 4.1 最推荐：先提交一份临时 commit 再转移

优点：

- 不会丢失未跟踪文件
- Windows 电脑上可以直接 `git pull`
- 后续更容易回滚和比较

### 4.2 次推荐：整个项目目录完整拷贝/打包

前提：

- 必须确保把 **untracked files** 也一起带走
- 不能只复制 git tracked 文件

### 4.3 当前 modified files

当前 `git diff --stat` 统计：

- `19 files changed, 634 insertions(+), 97 deletions(-)`

当前 modified files：

- `README.md`
- `docs/testing/test-plan.md`
- `pyproject.toml`
- `src/screen_human_lab/cli.py`
- `src/screen_human_lab/config.py`
- `src/screen_human_lab/inference/factory.py`
- `src/screen_human_lab/overlay/__init__.py`
- `src/screen_human_lab/overlay/appkit_overlay.py`
- `src/screen_human_lab/pipeline/__init__.py`
- `src/screen_human_lab/pipeline/gated_runtime.py`
- `src/screen_human_lab/pipeline/overlay.py`
- `src/screen_human_lab/pipeline/runtime.py`
- `src/screen_human_lab/tracking/template_match.py`
- `tests/test_cli_runtime.py`
- `tests/test_config.py`
- `tests/test_factory.py`
- `tests/test_gated_runtime.py`
- `tests/test_project_files.py`
- `tests/test_template_tracker.py`

### 4.4 当前 untracked files

这些文件如果不一起带走，会造成状态断裂：

- `configs/realtime_win_cpu.yaml`
- `configs/realtime_win_cuda.yaml`
- `configs/realtime_win_overlay_cuda.yaml`
- `docs/plans/2026-03-12-windows-stability-preview-design.md`
- `docs/plans/2026-03-12-windows-stability-preview.md`
- `src/screen_human_lab/inference/torch_cuda.py`
- `src/screen_human_lab/overlay/windows_overlay.py`
- `src/screen_human_lab/pipeline/global_motion.py`
- `src/screen_human_lab/pipeline/lock_state.py`
- `src/screen_human_lab/pipeline/target_filter.py`
- `src/screen_human_lab/pipeline/target_scoring.py`
- `tests/test_global_motion.py`
- `tests/test_lock_state.py`
- `tests/test_preview_runtime.py`
- `tests/test_target_filter.py`
- `tests/test_target_scoring.py`
- `tests/test_windows_overlay.py`
- `yolo11n.pt`

特别说明：

- `models/yolo11n.pt` 当前已经存在于 `models/` 目录中，是配置里默认使用的模型路径。
- 根目录下的 `yolo11n.pt` 是额外存在的未跟踪文件，目前不是主配置的标准路径。
- 如果迁移到 Windows，**优先保证 `models/yolo11n.pt` 存在**；根目录那个 `yolo11n.pt` 不是必须依赖项。

---

## 5. Windows 机器接手时的推荐步骤

下面是最实用的接手顺序。

### 5.1 第一步：把当前工作树完整带过去

二选一：

1. Git 临时提交后推送/拷贝
2. 直接复制整个项目文件夹，包括 `.git` 和 untracked files

### 5.2 第二步：确认 Python 版本

当前 `pyproject.toml` 要求：

- `Python >=3.10,<3.14`

建议优先：

- `Python 3.10.x` 或 `Python 3.11.x`

原因：

- 与当前项目依赖兼容性更稳
- 对 `torch` / `ultralytics` / `opencv-python` 组合更友好

### 5.3 第三步：创建 Windows 虚拟环境

推荐示例：

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
```

### 5.4 第四步：安装依赖

这里有一个**重要注意点**：

当前 `pyproject.toml` 里的 `runtime` extra 含有：

- `pyobjc-framework-Cocoa>=10.3`

这个是 macOS 专用依赖。**在 Windows 上直接执行 `pip install -e ".[runtime,cuda,dev]" 很可能失败。**

所以在 Windows 上，当前建议先用下面的临时安装方式：

```powershell
python -m pip install -e .
python -m pip install "mss>=10.0.0" "Pillow>=11.0.0" "opencv-python>=4.10.0,<4.12" "torch>=2.5.0" "ultralytics>=8.3.0" "pytest>=8.3.0"
```

如果你想验证 CPU 路线，再补：

```powershell
python -m pip install "onnxruntime>=1.20.0"
```

### 5.5 第五步：确认模型文件

至少保证下面这个文件存在：

- `models/yolo11n.pt`

如果你要跑 CPU 配置，还需要：

- `models/yolo11n.onnx`

注意：

- 当前仓库里 **没有看到** `models/yolo11n.onnx`。
- 所以 `configs/realtime_win_cpu.yaml` 目前更像“预留配置”，不是立即可运行的完整路线。

### 5.6 第六步：优先跑测试

接手之后，先验证 Python 逻辑没有在转移过程中损坏：

```powershell
pytest -q
```

如果你只想先验证 Windows 路线，可先跑：

```powershell
pytest tests/test_cli_runtime.py tests/test_preview_runtime.py tests/test_windows_overlay.py -q
```

### 5.7 第七步：先跑稳定预览，再跑原生 overlay

推荐顺序：

1. 先跑预览模式：

```powershell
python -m screen_human_lab.cli --config configs/realtime_win_cuda.yaml
```

2. 确认预览模式稳定后，再跑 Win32 overlay：

```powershell
python -m screen_human_lab.cli --config configs/realtime_win_overlay_cuda.yaml
```

原因：

- 预览模式更容易看日志、看状态、调参数
- overlay 模式涉及 Win32 GUI 细节，先把稳定 runtime 证实没问题，再看窗口层问题，排障效率更高

---

## 6. 真实 Windows 机器上优先要验证什么

这是换机后最应该优先做的人工验证清单。

### 6.1 P0：确认 CUDA 路线真的跑在 GTX 1650 Ti 上

检查点：

1. `backend: auto` 是否解析成 CUDA
2. `TorchCudaBackend` 是否成功加载模型
3. 实际 FPS 是否满足预期
4. `confidence_threshold=0.35` 是否过高或过低
5. `input_size=640` 对 1650 Ti 是否合适

建议：

- 如果 FPS 不理想，第一优先尝试把 `input_size` 降到 `512` 或 `416` 做 A/B 测试。
- 第二优先再调整 `target_fps`。

### 6.2 P0：验证稳定预览链路

检查点：

1. 快速晃动屏幕内容时，框是否比旧逻辑更稳
2. 是否仍然容易误切目标
3. 锁定后丢失 1~5 帧时是否能自然恢复
4. 是否在“恢复中”阶段出现明显跳框
5. `dx/dy` 是否与视觉方向一致

### 6.3 P0：验证 Win32 ROI overlay 真机表现

检查点：

1. 窗口是否准确贴合 ROI 区域
2. 窗口是否始终置顶
3. 背景透明是否正确
4. 边框绘制是否稳定
5. 检测框是否与 ROI 内目标位置严格对齐
6. `L` 键切换是否存在重复触发或粘连
7. 右键按住/释放是否立即开启或清空检测
8. 是否存在明显闪烁
9. 是否存在拖影或绘制延迟
10. 关闭窗口时是否能干净退出线程

### 6.4 P0：验证光标跟随没有引入新的不稳定

检查点：

1. 目标锁定后，光标是否沿预期方向跟随
2. 高速晃动时，光标是否发生抖动放大
3. `cursor_follow_speed` 是否过大导致超调
4. `cursor_follow_min_distance` 是否过小导致微抖

建议初始调参方向：

- 如果跟随太冲：降低 `cursor_follow_speed`
- 如果接近目标时仍抖：增大 `cursor_follow_min_distance`

---

## 7. 现在还没有完成，但下一步非常值得做的开发

下面按优先级排序。

### 7.1 第一优先级：把 Windows 路线从“代码完成”推进到“真机稳定”

这是现在最重要的事情。

建议顺序：

1. Windows 真机安装与依赖验证
2. 跑 `realtime_win_cuda.yaml`
3. 跑 `realtime_win_overlay_cuda.yaml`
4. 记录卡顿/闪烁/误锁/误切换问题
5. 针对真实问题微调稳定性参数

这个阶段**不要**急着引入 RL 或大模型。

### 7.2 第二优先级：修复 Windows 安装体验

当前明确存在一个工程层面的待办：

- `pyproject.toml` 中 `runtime` extra 包含 macOS 专用的 `pyobjc-framework-Cocoa`

建议后续改造：

1. 给 `pyobjc-framework-Cocoa` 加 Darwin 环境标记
2. 或者把 macOS overlay 依赖拆到独立 extra，比如：
   - `macos_overlay`
   - `windows_runtime`
   - `cuda_runtime`

这是一个很值得尽快修的点，因为它直接影响 Windows 新环境的冷启动体验。

### 7.3 第三优先级：继续优化 Win32 overlay 显示层

当前已经做到“能跑的 ROI 原生 overlay”，但还有明显优化空间：

1. 点击穿透
   - 当前不是优先目标，后续可加
   - 方向：`WS_EX_TRANSPARENT` 或条件式 hit-test

2. 部分覆盖 / 局部绘制
   - 当前是 ROI window 内整体透明底 + ROI 边框 + 检测框绘制
   - 后续可进一步减少无效绘制区域

3. 双缓冲/离屏绘制
   - 当前如果出现闪烁，可考虑 GDI 双缓冲
   - 或改成更低闪烁的绘制策略

4. 刷新节奏优化
   - 当前 `WINDOW_REFRESH_HZ = 60.0`
   - 可根据检测线程耗时和 Win32 message loop 行为进一步调节

5. 文本与状态信息增强
   - 当前只显示核心框和 `dx/dy`
   - 后续可显示：`state=locked/recovering`、`motion=(dx,dy)`、`fps`

### 7.4 第四优先级：继续提升非训练稳定性

在引入训练前，纯工程层仍然有很多可做优化：

1. 更强的全局运动估计
   - 当前是 phase correlation
   - 后续可对比：特征点匹配、仿射估计、稀疏光流

2. 更细粒度的时序约束
   - 根据连续帧中心偏移、速度、尺寸变化加更严格门控

3. 更好的目标切换保护
   - 当前已有评分体系
   - 后续可加“切换惩罚”或“最小保持时长”

4. 更稳的 bbox 滤波
   - 当前是指数平滑
   - 后续可尝试简化版 Kalman filter 或 alpha-beta filter

5. 更强的误检抑制
   - 可加入宽高比、面积变化、边缘截断惩罚等规则

### 7.5 第五优先级：数据记录与离线评估

在真正进入 ML/RL 之前，建议先做这个：

1. 数据记录器
   - 录制 ROI 帧序列
   - 保存检测输出
   - 保存锁定状态
   - 保存鼠标按键状态
   - 保存目标框轨迹

2. 离线回放器
   - 能对一段录制视频重复跑不同参数配置
   - 便于稳定性回归对比

3. 评估指标
   - 框中心抖动幅度
   - 目标 ID 切换次数
   - 丢锁恢复成功率
   - 有效锁定帧占比
   - 延迟/FPS

这个阶段很重要，因为没有稳定的数据记录和离线评估，就很难严肃推进 RL。

### 7.6 第六优先级：训练/RL 路线（仍然是后续项，不是当前主线）

关于你之前提到的 RL 和多模态方案，当前建议路线如下。

#### 7.6.1 现在为什么不建议立刻上 RL

原因：

1. 当前问题首先是实时视觉与稳定工程问题
2. 缺少标准化数据记录与回放闭环
3. 缺少稳定 reward 定义
4. 缺少 Windows 真机上的基线性能数据

所以现在直接上 RL，收益大概率不如继续把非训练链路做稳。

#### 7.6.2 如果后续真要做，推荐顺序

1. 先做数据记录器与离线评估
2. 先做 imitation / supervised baseline
3. 再尝试 RL 微调
4. 最后再考虑多模态辅助

#### 7.6.3 各方案在本项目中的合理定位

- `CLIP`
  - 更适合做目标语义重排序、类别确认、误检过滤
  - 不适合直接替代当前实时检测主链路

- `BLIP-2`
  - 更偏描述/理解，不适合作为实时主检测环

- `Segment Anything`
  - 可作为 ROI 内更精细轮廓/掩膜辅助
  - 但对你的硬件预算和实时性要求来说，不能直接无脑上主链路

- `LLaVA`
  - 更适合离线分析、标注辅助、错误案例归因
  - 不适合直接挂在实时环中

- `trl-fine-tuning`、`grpo-rl-training`、`openrlhf`
  - 这些属于训练框架/训练方法层
  - 前提是你先有数据、奖励和评估体系

- `pytorch-lightning`
  - 更适合整理训练代码结构

- `ray-train`
  - 更适合做多实验并行训练

- `mlflow`、`weights-and-biases`
  - 更适合做实验记录、参数对比、指标可视化

结论：

- 它们都**可以**成为后续体系的一部分
- 但当前阶段的最高回报项仍然是：
  - Windows 真机验证
  - 非训练稳定性继续优化
  - 数据记录与离线评估闭环

---

## 8. 下一次接手时，建议先看的关键代码文件

下面是恢复开发时最值得优先打开的文件及其作用。

### 8.1 入口与路由

- `src/screen_human_lab/cli.py`
  - 看平台如何分支到：
    - Windows overlay
    - macOS overlay
    - 稳定 preview session

### 8.2 配置模型

- `src/screen_human_lab/config.py`
  - 看后端自动选择规则
  - 看 `OverlayConfig`
  - 看 `TrackingConfig`
  - 看 `StabilityConfig`

### 8.3 Windows 原生 overlay

- `src/screen_human_lab/overlay/windows_overlay.py`
  - 看 ROI window 坐标计算
  - 看 worker 线程
  - 看 Win32 message loop
  - 看绘制逻辑
  - 看 `L` 键与右键门控

### 8.4 稳定检测主逻辑

- `src/screen_human_lab/pipeline/gated_runtime.py`
  - 看全局运动估计接入
  - 看单目标锁定
  - 看丢失恢复
  - 看本地/全局坐标输出

### 8.5 稳定 preview session

- `src/screen_human_lab/pipeline/runtime.py`
  - 看 `StablePreviewSession`

### 8.6 目标稳定性组件

- `src/screen_human_lab/pipeline/global_motion.py`
- `src/screen_human_lab/pipeline/target_scoring.py`
- `src/screen_human_lab/pipeline/target_filter.py`
- `src/screen_human_lab/pipeline/lock_state.py`
- `src/screen_human_lab/tracking/template_match.py`

### 8.7 配置入口

- `configs/realtime_win_cuda.yaml`
- `configs/realtime_win_overlay_cuda.yaml`
- `configs/realtime_win_cpu.yaml`

### 8.8 最关键测试

- `tests/test_preview_runtime.py`
- `tests/test_windows_overlay.py`
- `tests/test_cli_runtime.py`
- `tests/test_gated_runtime.py`
- `tests/test_template_tracker.py`

---

## 9. 当前已知风险与注意事项

### 9.1 Windows 安装依赖风险

- `pyobjc-framework-Cocoa` 在 Windows 上不合适
- 当前需要手工绕过 `runtime` extra 安装问题

### 9.2 CPU 配置不一定可立即运行

- `configs/realtime_win_cpu.yaml` 指向 `models/yolo11n.onnx`
- 这个模型文件当前仓库里没有看到
- 所以 CPU 配置目前是“预留路线”，不是现成可验证方案

### 9.3 Win32 overlay 还缺少真机人工 smoke 测试

- 单元测试通过不等于 GUI 体验已经完全没问题
- 真机上仍可能暴露：
  - 闪烁
  - 键盘轮询边界问题
  - 线程退出清理问题
  - DPI/缩放问题
  - 窗口置顶或透明异常

### 9.4 当前未提交

- 现在这不是一个 Git 上可复现的干净节点
- 如果迁移时漏掉 untracked files，会直接导致状态不连续

---

## 10. 下一会话建议直接使用的启动提示词

如果你在另一台 Windows 机器上重新开启会话，建议直接告诉新会话：

```text
先阅读 docs/plans/2026-03-12-windows-continuation-handoff.md，按里面的 Windows 接手流程继续。
当前目标不是训练，而是先在 Windows + GTX 1650 Ti 上把 realtime_win_cuda.yaml 和 realtime_win_overlay_cuda.yaml 跑稳。
优先做真机验证、参数调优、Win32 overlay 修正，不要先扩展 RL 训练栈。
```

如果你希望新会话继续做下一步开发，可以再补一句：

```text
先检查 Windows 安装依赖问题，再验证 Win32 ROI overlay 的真实表现，记录问题后继续优化显示稳定性和锁定稳定性。
```

---

## 11. 当前阶段的结论

一句话总结当前状态：

> Windows 优先、非训练稳定性优先的主线已经从方案进入代码，稳定 preview 和 Win32 ROI overlay 两条路径都已落地，并且在当前开发环境中通过了完整测试；下一阶段的核心不再是“写新方案”，而是“在真实 Windows + GTX 1650 Ti 机器上验证、修正、调优”。

