README
======

What is WAVES for ?
-------------------

WAVES stands for "\ **W**\ eb \ **A**\ pplication for \ **V**\ ersatile and \ **E**\ asy online bioinformatic \ **S**\ ervices."

WAVES is a dedicated Django based web application to ease bioinformatic tools integration through web interfaces in
order to provide the scientific community with bioinformatic services.

It is aimed to help you easily present, publish and give access on the web to any bioinformatic tool.


Features
--------

- Create and manage your services execution over platform such as Galaxy, DRMAA clusters (SGE), Direct script execution, API calls to other services, remote calls to other platforms via ssh, etc.
- Easily presents these tools in a nice frontend based on Bootstrap3, Bootstrap4 and soon Material Design
- Follow and manage remote REST API access to your service platform
- Manage user's access to your services


> Note: \
> WAVES main component is WAVES-core.\
> The second component is WAVES-Galaxy. It is a WAVES adapter to interact with Galaxy instances.\
> WAVES-demo is a custom version of WAVES-core for demo purpose only.

Side projects
-------------

- WAVES-galaxy adapter `<https://www.github.com/lirmm/waves-galaxy>`_
- WAVES-demo project `<https://www.github.com/lirmm/waves-demo>`_


Installation
------------

- You can use WAVES-core as a stand alone application.
- WAVES-core comply to standard reusable project layout for Django. So you may include it as a dependency in your own django project
- Complete documentation available on `readthedocs <https://waves-core.readthedocs.io>`_


Just have a try
----------------

A pre-installed WAVES-core with configured services is available in a `Singularity image <http://singularity.lbl.gov>`_.
This is a good way to test a fully operating WAVES-core system with a very simple "Hello World" service and another one that run Phyml 3.1.
Caution, this image is just for tests. All data will be loosed when singularity instance will be stopped

Singularity installation : `on Linux <http://singularity.lbl.gov/install-linux>`_ or `Mac <http://singularity.lbl.gov/install-mac>`_.

Download WAVES test Singularity image : `wavetest.simg <http://www.atgc-montpellier.fr/download/binaries/waves/wavestest.simg>`_

Example for a Debian / Ubuntu 16.04 or after :

Install Singularity :
```angular2html
sudo wget -O- http://neuro.debian.net/lists/xenial.us-ca.full | sudo tee /etc/apt/sources.list.d/neurodebian.sources.list
sudo apt-key adv --recv-keys --keyserver hkp://pool.sks-keyservers.net:80 0xA5D32F012649A5A9
sudo apt-get update
sudo apt-get install -y singularity-container
```

Get and use wavestest.simg (caution, you need to be sudoer to start an instance)
```angular2html
cd ~/Documents
wget http://www.atgc-montpellier.fr/download/binaries/waves/wavestest.simg
sudo singularity instance.start wavestest.simg waves
sudo singularity run instance://waves
```

Image is launched and WAVES-core is running. Open localhost:8000 on your favorite browser. Login with "admin" and "motdepasse".

At the end of your tests
```angular2html
sudo singularity instance.stop waves
```


Support
-------

If you are having issues, (or just want to say hello): we have a mailing list located at: waves@lirmm.fr
