# Introduction

<h3 align="center">Quantifarm Benchmarking Tool UnitTests</h3>

<p align="center">
  Unit Testing for the Tool EndPoints.
</p>

<p align="center">
  The following Technolgies / APIs / Libraries are utilised:
  <br>
  Python 3 : <a href="https://docs.python.org/3/"><strong>Explore Python 3.6+ docs »</strong></a>
  <br>
  FastAPI : <a href="https://fastapi.tiangolo.com/"><strong>FastAPI »</strong></a>
</p>

## Libraries needed for Unit Testing
```console
$ pip install requests
$ pip install pytest pytest-html
$ pip install jsonschema
$ pip install pytest-asyncio
```

## Execution
To execute the test , navigate into the folder where the "test_scenario.py" file resides and execute the following command : 
```console
$ pytest --tb=short -rP test_scenario.py
```
