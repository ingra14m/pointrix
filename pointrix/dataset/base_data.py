import torch
import numpy as np
from PIL import Image
from pathlib import Path
from abc import abstractmethod
from torch.utils.data import Dataset
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Union, List

from pointrix.utils.config import parse_structured
from pointrix.camera.camera import Camera, TrainableCamera
from pointrix.dataset.utils.dataset_utils import force_full_init, getNerfppNorm


@dataclass
class BaseDataFormat:
    image_filenames: List[Path]
    """camera image filenames"""
    Cameras: List[Camera]
    """camera parameters"""
    metadata: Dict[str, Any] = field(default_factory=lambda: dict({}))
    """other information that is required for the dataset"""

    def __getitem__(self, item):
        return self.image_filenames[item], self.Cameras[item]

    def __len__(self):
        return len(self.image_filenames)


class BaseReFormatData:

    def __init__(self, data_root: Path,
                 split: str = "train"):
        self.data_root = data_root
        self.split = split
        self.data_list = self.load_data_list(self.split)

    def load_data_list(self, split) -> BaseDataFormat:
        camera = self.load_camera(split=split)
        image_filenames = self.load_image_filenames(camera, split=split)
        metadata = self.load_metadata(split=split)
        data = BaseDataFormat(image_filenames, camera, metadata)
        return data

    @abstractmethod
    def load_camera(self, split) -> List[Camera]:
        raise NotImplementedError

    @abstractmethod
    def load_image_filenames(self, split) -> list[Path]:
        raise NotImplementedError

    @abstractmethod
    def load_metadata(self, split) -> Dict[str, Any]:
        raise NotImplementedError


# TODO: support cached dataset and lazy init
# TODO: support different dataset (Meta information (depth) support)
class BaseImageDataset(Dataset):
    def __init__(self, format_data: BaseDataFormat) -> None:
        self.format_data = format_data
        cameras = self.format_data.Cameras
        Rs, Ts = [], []
        for camera in cameras:
            Rs.append(camera.R)
            Ts.append(camera.T)
        self.Rs = torch.stack(Rs, dim=0)
        self.Ts = torch.stack(Ts, dim=0)
        self.radius = getNerfppNorm(self.Rs.numpy(), self.Ts.numpy())["radius"]

    # TODO: full init
    def __len__(self):
        return len(self.format_data)

    def __getitem__(self, idx):
        image_file_name, camera = self.format_data[idx]
        image = self.load_image(image_file_name, camera.bg)
        camera.height = image.shape[1]
        camera.width = image.shape[2]
        return {"image": image,
                "camera": asdict(camera)}

    def load_image(self, image_filename, bg=[1., 1., 1.]):
        pil_image = Image.open(image_filename)
        # shape is (h, w) or (h, w, 3 or 4)
        image = np.array(pil_image, dtype="uint8") / 255.0

        if len(image.shape) == 2:
            image = image[:, :, None].repeat(3, axis=2)
        assert len(image.shape) == 3
        assert image.shape[2] in [
            3, 4], f"Image shape of {image.shape} is in correct."

        if image.shape[2] == 4:
            image = image[:, :, :3] * image[:, :, 3:4] + \
                bg * (1 - image[:, :, 3:4])

        image_tensor = torch.Tensor(image).float()
        return image_tensor.permute(2, 0, 1)


class BaseDataPipline:
    @dataclass
    class Config:
        # Datatype
        data_path: str = "data"
        data_type: str = "nerf"
        cached_image: bool = False
        shuffle: bool = True
        batch_size: int = 1
        num_workers: int = 1
    cfg: Config

    def __init__(self, cfg):
        self.cfg = parse_structured(self.Config, cfg)
        self._fully_initialized = False

        # TODO: use registry
        if self.cfg.data_type == "colmap":
            from pointrix.dataset.colmap_data import ColmapReFormat as ReFormat
        elif self.cfg.data_type == "nerf_synthetic":
            from pointrix.dataset.nerf_data import NerfReFormat as ReFormat

        self.train_format_data = ReFormat(
            data_root=self.cfg.data_path, split="train").data_list
        self.validation_format_data = ReFormat(
            data_root=self.cfg.data_path, split="val").data_list

        self.loaddata()

    # TODO use rigistry
    def get_training_dataset(self):
        # TODO: use registry
        self.training_dataset = BaseImageDataset(
            format_data=self.train_format_data)

    def get_validation_dataset(self):
        self.validation_dataset = BaseImageDataset(
            format_data=self.validation_format_data)

    def loaddata(self):
        self.get_training_dataset()
        self.get_validation_dataset()

        self.training_loader = torch.utils.data.DataLoader(
            self.training_dataset,
            batch_size=self.cfg.batch_size,
            shuffle=self.cfg.shuffle,
            num_workers=self.cfg.num_workers,
            pin_memory=True,
        )
        self.validation_loader = torch.utils.data.DataLoader(
            self.validation_dataset,
            batch_size=self.cfg.batch_size,
            shuffle=self.cfg.shuffle,
            num_workers=self.cfg.num_workers,
            pin_memory=True,
        )
        self.iter_train_image_dataloader = iter(self.training_loader)
        self.iter_val_image_dataloader = iter(self.validation_loader)

    def next_train(self, step=int):
        try:
            return next(self.iter_train_image_dataloader)
        except StopIteration:
            self.iter_train_image_dataloader = iter(self.training_loader)
            return next(self.iter_train_image_dataloader)

    def next_val(self, step=int):
        try:
            return next(self.iter_val_image_dataloader)
        except StopIteration:
            self.iter_val_image_dataloader = iter(self.validation_loader)
            return next(self.iter_val_image_dataloader)

    @property
    def training_dataset_size(self):
        return len(self.training_dataset)

    @property
    def validation_dataset_size(self):
        return len(self.validation_dataset)

    def get_param_groups(self):
        raise NotImplementedError
