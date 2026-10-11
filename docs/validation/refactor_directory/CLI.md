# R11–R14 命令

```powershell
python tools/refactor/architecture.py D:/ar-r11-r14/architecture.json
python -m unittest tests/test_modularity.py
python tools/refactor/build_wheel.py --output D:/ar-r11-r14/wheel
```

架构结果覆盖递归 import 图和动态导入记录；历史 completion/history 工具继续使用固定 Git SHA，不刷新旧材料。最终验收必须使用新的 wheel 和新的输出目录。
