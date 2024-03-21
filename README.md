<div align="center">
  <p align="center">
      <picture>
      <source srcset="https://github.com/pointrix-project/pointrix/assets/32637882/cf58c589-8808-4b8f-8941-982b8a688b8c" media="(prefers-color-scheme: dark)">
      <source srcset="https://github.com/pointrix-project/pointrix/assets/32637882/e0bd7ce3-fbf3-40f3-889c-7c882f3eed20" media="(prefers-color-scheme: light)">
      <img alt="Pointrix" src="https://github.com/pointrix-project/pointrix/assets/32637882/e0bd7ce3-fbf3-40f3-889c-7c882f3eed20" width="80%">
      </picture>
  </p>
  <p align="center">
    A differentiable point-based rendering library.
    <br />
    <a href="https://pointrix-project.github.io/pointrix/">
    <strong>Document🏠</strong></a>  | 
    <a href="https://pointrix-project.github.io/pointrix/">
    <strong>Paper(Comming soon)📄</strong></a> | 
    <a href="https://github.com/pointrix-project/dptr">
    <strong>DPTR Backend🌐</strong></a>
    <br />
    <br />
    <!-- <a href="https://github.com/othneildrew/Best-README-Template">View Demo</a>
    ·
    <a href="https://github.com/othneildrew/Best-README-Template/issues">Report Bug</a>
    ·
    <a href="https://github.com/othneildrew/Best-README-Template/issues">Request Feature</a> -->
  </p>
</div>

[![Hits](https://hits.seeyoufarm.com/api/count/incr/badge.svg?url=https%3A%2F%2Fgithub.com%2Fpointrix-project%2Fpointrix&count_bg=%2396114C&title_bg=%23555555&icon=&icon_color=%23E7E7E7&title=visitors&edge_flat=false)](https://hits.seeyoufarm.com)
![Hits](https://img.shields.io/github/stars/pointrix-project/pointrix)
![Static Badge](https://img.shields.io/badge/Pointrix_document-Pointrix_document?color=hsl&link=https%3A%2F%2Fpointrix-project.github.io%2Fpointrix)




Pointrix is a differentiable point-based rendering library which has following properties:

- **Highly Extensible**:
  - Python API
  - Modular design for both researchers and beginners
  - Implementing your own method without touching CUDA
- **Powerful Backend**:
  - CUDA Backend
  - Forward Anything: rendering image, depth, normal, optical flow, etc.
  - Backward Anything: optimizing even intrinsics and extrinsics.
- **Rich Features**:
  - 3D Reconstruction: [Vanilla 3DGS](https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/3d_gaussian_splatting_high.pdf) (Siggraph 2023), [Relightable 3DGS](https://arxiv.org/pdf/2311.16043.pdf)(WIP)
  - 4D Reconstruction: [Deformable 3DGS](https://arxiv.org/abs/2309.13101) (CVPR 2024), [Gaussian-Flow](https://arxiv.org/abs/2312.03431) (CVPR 2024, WIP)
  - 3D Generation: [GSGen](https://arxiv.org/pdf/2309.16585.pdf) (CVPR 2024, WIP), [DreamGaussian](https://arxiv.org/pdf/2309.16653.pdf) (ICLR 2024, TBD), [LGM](https://arxiv.org/pdf/2402.05054.pdf) (arXiv 2024, TBD)
  - 4D Generation: [STAG4D]() (arXiv 2024, WIP), [DreamGaussian4D](https://arxiv.org/pdf/2312.17142.pdf) (arXiv 2023, TBD)
  - ...




<!-- - **Powerful Backend**:
  - **Render Anything**: image, depth, normal, optical flow, etc.
  - **Backward Anything**: including camera parameters.
  - Modular design and easy to modify, support open-gl and opencv camera.
- **Rich Feature**:
  - **3D Reconstruction**: 
      - [Vanilla 3DGS](https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/3d_gaussian_splatting_high.pdf) (Siggraph 2023)
  - **3D Generation**: 
      - [MVDream](https://arxiv.org/abs/2308.16512) (arXiv 2023)
  - **4D Reconstruction**: 
      - [Deformable 3DGS](https://arxiv.org/abs/2309.13101) (CVPR 2024)
      - [Gaussian-Flow](https://arxiv.org/abs/2312.03431) (CVPR 2024)
  - **4D Generation**: 
      - [STAG4D]() (arXiv 2024)
  - **...**
- **Highly Extensible and Designed for Research**:
  - Pointrix adopts a modular design, with clear structure and easy extensibility. 
  - Only few codes need to be modified if you want to add a new method.  -->


<div style="display:flex;">
  <img src="https://github.com/pointrix-project/pointrix/assets/32637882/61795e5a-f91a-4a2a-b6ce-9a341a16145e" width="30%" />
  <img src="https://github.com/pointrix-project/pointrix/assets/32637882/616b7af8-3a8a-455a-ac1e-a62e9dc146d2" width="30%" />
  <img src="https://github.com/pointrix-project/pointrix/assets/32637882/928a142e-38cb-48e6-847b-1c6d4b95f7a3" width="30%" />
</div>

## Comparation with original 3D gaussian code

### nerf_synthetic dataset (PSNR)

| Method                  | lego        | chair        | ficus        | drums        | hotdog        | ship        | materials        | mic        | average        |
| -----------             | ----------- | ----------- | ----------- | ----------- | ----------- | ----------- | ----------- | ----------- | ----------- |
| Pointrix | 35.84       | 36.12       | 35.02       | 26.18       | 37.81       | 30.98       | 29.95       | 35.34       |  33.40       |
| [original](https://github.com/graphdeco-inria/gaussian-splatting)        | 35.88        | 35.92        | 35.00        | 26.21        | 37.81        | 30.95        | 30.02        | 35.35        |   33.39       |

we obtain the result of 3D gaussian code by running following command in their repository.
```bash
 python train.py -s nerf_synthetic_root --eval -w
```

## Quickstart

### Installation


Clone pointrix:

```bash
git clone https://github.com/pointrix-project/pointrix.git
```

Create a new conda environment with pytorch:

```bash
conda create -n pointrix python=3.9
conda activate pointrix
conda install pytorch==2.1.1 torchvision==0.16.1 pytorch-cuda=12.1 -c pytorch -c nvidia
```

Install DPTR backend and dependencies:

```bash
# note: can also switch to the original 3DGS diff-gaussian-rasterization 
git clone https://github.com/pointrix-project/dptr.git --recursive
cd dptr
pip install .
```
```bash
# Install simple knn
git clone https://gitlab.inria.fr/bkerbl/simple-knn.git
cd simple-knn
python setup.py install
pip install .
```

Install Pointrix:

```
cd pointrix
pip install -r requirements.txt
pip install -e .
```


###  Train Your First 3D Gaussian

#### NeRF-Lego (NeRF-Synthetic format dataset)
Download the lego data:

```bash
wget http://cseweb.ucsd.edu/~viscomp/projects/LF/papers/ECCV20/nerf/nerf_example_data.zip
```

Run the following (with adjusted data path in the config):

```bash
cd pointrix/projects/gaussian_splatting
python launch.py --config ./configs/nerf_dptr.yaml

# you can also run the following for the original 3DGS kernel
# python launch.py --config ./configs/nerf.yaml
```

#### Mip-NeRF 360 (Colmap format dataset)
Download the [data](http://storage.googleapis.com/gresearch/refraw360/360_v2.zip) and run:

```bash
cd pointrix/projects/gaussian_splatting
python launch.py --config ./configs/colmap_dptr.yaml

# you can also run the following for the original 3DGS kernel
# python launch.py --config ./configs/colmap.yaml
```

## Advanced Approaches

#### Deformable 3D Gaussian
1. Download the iphone dataset and put it in your folder:
https://drive.google.com/drive/folders/1cBw3CUKu2sWQfc_1LbFZGbpdQyTFzDEX

2. Run the following command to train the model (...data path in the config file...):

```bash
cd pointrix/projects/deformable_gaussian
python launch.py --config deform.yaml
```

#### Gaussian-Flow (WIP)

#### GSGen (WIP)

#### STAG4D (WIP)

#### Relightable 3DGS (WIP)


## Release Plans
- [ ] GUI for visualization (this week).
- [ ] Implementataion of Gaussian-Flow (CVPR 2024) (this week).
- [ ] Implementataion of GSGen with MVDream SDS (this week).
- [ ] Camera optimization (this week).
- [ ] Introduction video
- [ ] Implementataion of Relightable Gaussian (arXiv 2023).

Welcome to discuss with us and submit PR on new ideas and methods.



## Contributors
<a href="https://github.com/pointrix-project/pointrix/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=pointrix-project/pointrix" />
</a>

Made with [contrib.rocks](https://contrib.rocks).

