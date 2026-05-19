"""Pallas — 知识工程工具集统一入口

一条命令拉通 ToolForge 工具匹配、OntoDerive 事实推导、Minerva 深度研究。
"""

__version__ = "0.1.0"
"""
Pallas — 知识工程工具集统一入口。

跨项目桥接:
- pallas → ontoderive: 调用 ontoderive CLI (match/derive/check/toolforge)
- pallas → agora: 调用 agora CLI (register/pipeline/pipelines)
- pallas → sophia: 共享知识工程范式，通过 sophia.compiler 编译研究范式
- pallas → minerva: pipeline 流程可接入 minerva 深度研究
"""
