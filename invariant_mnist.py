import torch
import torchvision
import torchvision.transforms as transforms
from pytorch_lightning import LightningModule, Trainer
import matplotlib.pyplot as plt
import numpy as np
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from pytorch_lightning.metrics.functional import accuracy
from high_order_layers_torch.PolynomialLayers import *
from high_order_layers_torch.layers import *
from omegaconf import DictConfig, OmegaConf
import hydra
import os

transform = transforms.Compose(
    [transforms.ToTensor(), transforms.Normalize((0.5,), (0.5,))])

trainset = torchvision.datasets.MNIST(
    root='./data', train=True, download=True, transform=transform)
trainloader = torch.utils.data.DataLoader(
    trainset, batch_size=4, shuffle=True, num_workers=2)

testset = torchvision.datasets.MNIST(
    root='./data', train=False, download=True, transform=transform)
testloader = torch.utils.data.DataLoader(
    testset, batch_size=4, shuffle=False, num_workers=2)

classes = ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9')


class Net(LightningModule):
    def __init__(self, cfg):
        super().__init__()
        self._cfg = cfg
        self._batch_size = cfg.batch_size
        self.criterion = nn.CrossEntropyLoss()
        self._data_dir = f"{hydra.utils.get_original_cwd()}/data"

        self.layer1 = high_order_fc_layers(
            layer_type=cfg.layer_type, n=cfg.n, in_features=784, out_features=100, segments=cfg.segments)
        self.layer2 = nn.LayerNorm(100)
        self.layer3 = high_order_fc_layers(
            layer_type=cfg.layer_type, n=cfg.n, in_features=100, out_features=10, segments=cfg.segments)
        self.layer4 = nn.LayerNorm(10)

    def forward(self, x):
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)
        output = F.log_softmax(x, dim=1)
        return output

    def training_step(self, batch, batch_idx):
        x, y = batch
        x_new = x.view(x.shape[0], -1)
        y_hat = self(x_new)
        return F.cross_entropy(y_hat, y)

    def train_dataloader(self):
        trainset = torchvision.datasets.MNIST(
            root=self._data_dir, train=True, download=True, transform=transform)
        return torch.utils.data.DataLoader(trainset, batch_size=self._batch_size, shuffle=True, num_workers=10)

    def test_dataloader(self):
        testset = torchvision.datasets.MNIST(
            root=self._data_dir, train=False, download=True, transform=transform)
        return torch.utils.data.DataLoader(testset, batch_size=self._batch_size, shuffle=False, num_workers=10)

    def validation_step(self, batch, batch_idx):
        return self.eval_step(batch, batch_idx, 'val')

    def eval_step(self, batch, batch_idx, name):
        x, y = batch
        x_new = x.view(x.shape[0], -1)
        logits = self(x_new)
        loss = F.nll_loss(logits, y)
        preds = torch.argmax(logits, dim=1)
        acc = accuracy(preds, y)

        # Calling self.log will surface up scalars for you in TensorBoard
        self.log(f'{name}_loss', loss, prog_bar=True)
        self.log(f'{name}_acc', acc, prog_bar=True)
        return loss

    def test_step(self, batch, batch_idx):
        # Here we just reuse the validation_step for testing
        return self.eval_step(batch, batch_idx, 'test')

    def configure_optimizers(self):
        return optim.Adam(self.parameters(), lr=0.001)


@hydra.main(config_name="./config/invariant_mnist")
def invariant_mnist(cfg: DictConfig):
    print(OmegaConf.to_yaml(cfg))
    print("Working directory : {}".format(os.getcwd()))
    print(f"Orig working directory    : {hydra.utils.get_original_cwd()}")
    trainer = Trainer(max_epochs=100, gpus=1)
    model = Net(cfg)
    trainer.fit(model)
    print('testing')
    trainer.test(model)
    print('finished testing')


if __name__ == "__main__":
    invariant_mnist()
