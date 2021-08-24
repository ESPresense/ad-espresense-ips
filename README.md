# ESPresense - Ips Solver

Appdaemon app that attempts to solve indoor position (x,y,z) with multiple ESPresense stations using trilateralization

For this to work you need to add this to your appdaemon config:
```
system_packages:
  - py3-numpy
  - py3-scipy
python_packages:
  - numpy
  - scipy
```
