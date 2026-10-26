@echo off
cd /d "%~dp0.."
uv run --with jupyter --with ipywidgets --with numpy --with matplotlib jupyter notebook jupyter_notebooks/demo1_holonomy_interactive.ipynb
