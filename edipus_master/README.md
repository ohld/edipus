# Edipus

## What is it
Sources of Edipus project.

## Getting started with Edipus

To install dependencies, train your personal identificator and validate webcam photo, run

  ```
  ./install-deps.sh
  ./train.py
  ./validate.py
  ```

## Files description

### main_app.py:

* GUI windows classes

* Singnals and Slots of this classes

### exec_thread.py:

* Main calculation thread

* Working with neuron network

* Working with vk_requests

### vk_requests.py:

* HTTPS requests for VK.com

* Logging in VK.com

* Downloading photots from VK.com

### face.py:
module with implementation of FACE class, used for training network.

### permission_control.py:
rewrited C module from **../permission control** folder.

