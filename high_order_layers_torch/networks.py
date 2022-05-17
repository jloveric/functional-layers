import torch.nn as nn
from torch import Tensor
from high_order_layers_torch.layers import (
    high_order_convolution_layers,
    high_order_convolution_transpose_layers,
    high_order_fc_layers,
)
from typing import Any, Callable, List, Union
from high_order_layers_torch.PolynomialLayers import interpolate_polynomial_layer
import torch


class HighOrderMLP(nn.Module):
    def __init__(
        self,
        layer_type: str,
        n: str,
        in_width: int,
        out_width: int,
        hidden_layers: int,
        hidden_width: int,
        scale: float = 2.0,
        n_in: int = None,
        n_out: int = None,
        n_hidden: int = None,
        rescale_output: bool = False,
        periodicity: float = None,
        non_linearity=None,
        in_segments: int = None,
        out_segments: int = None,
        hidden_segments: int = None,
        normalization: Callable[[Any], Tensor] = None,
    ) -> None:
        """
        Args :
            layer_type: Type of layer
                "continuous", "discontinuous",
                "polynomial", "fourier",
                "product", "continuous_prod",
                "discontinuous_prod"
            n:  Base number of nodes (or fourier components).  If none of the others are set
                then this value is used.
            in_width: Input width.
            out_width: Output width
            hidden_layers: Number of hidden layers.
            hidden_width: Number of hidden units
            scale: Scale of the segments.  A value of 2 would be length 2 (or period 2)
            n_in: Number of input nodes for interpolation or fourier components.
            n_out: Number of output nodes for interpolation or fourier components.
            n_hidden: Number of hidden nodes for interpolation or fourier components.
            rescale_output: Whether to average the outputs
            periodicity: Whether to make polynomials periodic after given length.
            non_linearity: Whether to apply a nonlinearity after each layer (except output)
            in_segments: Number of input segments for each link.
            out_segments: Number of output segments for each link.
            hidden_segments: Number of hidden segments for each link.
            normalization: Normalization to apply after each layer (before any additional nonlinearity).
        """
        super().__init__()
        layer_list = []
        n_in = n_in or n
        n_hidden = n_hidden or n
        n_out = n_out or n

        input_layer = high_order_fc_layers(
            layer_type=layer_type,
            n=n_in,
            in_features=in_width,
            out_features=hidden_width,
            segments=in_segments,
            rescale_output=rescale_output,
            scale=scale,
            periodicity=periodicity,
        )
        layer_list.append(input_layer)
        for i in range(hidden_layers):
            if normalization is not None:
                layer_list.append(normalization)
            if non_linearity is not None:
                layer_list.append(non_linearity())

            hidden_layer = high_order_fc_layers(
                layer_type=layer_type,
                n=n_hidden,
                in_features=hidden_width,
                out_features=hidden_width,
                segments=hidden_segments,
                rescale_output=rescale_output,
                scale=scale,
                periodicity=periodicity,
            )
            layer_list.append(hidden_layer)

        if non_linearity is not None:
            layer_list.append(non_linearity())
        if non_linearity is not None:
            layer_list.append(non_linearity())
        output_layer = high_order_fc_layers(
            layer_type=layer_type,
            n=n_out,
            in_features=hidden_width,
            out_features=out_width,
            segments=out_segments,
            rescale_output=rescale_output,
            scale=scale,
            periodicity=periodicity,
        )
        layer_list.append(output_layer)
        print("layer_list", layer_list)
        self.model = nn.Sequential(*layer_list)

    def forward(self, x: Tensor) -> Tensor:
        return self.model(x)


class HighOrderFullyConvolutionalNetwork(nn.Module):
    def __init__(
        self,
        layer_type: Union[List[str], str],
        n: List[int],
        channels: List[int],
        segments: List[int],
        kernel_size: List[int],
        rescale_output: bool = False,
        periodicity: float = None,
        normalization: Callable[[Any], Tensor] = None,
    ) -> None:
        """
        Args :

        """
        super().__init__()

        if len(channels) < 2:
            raise ValueError(
                f"Channels list must have at least 2 values [input_channels, output_channels]"
            )

        if (
            len(channels)
            == len(segments)
            == len(kernel_size)
            == len(layer_type)
            == len(n)
            is False
        ):
            raise ValueError(
                f"Lists for channels {len(channels)}, segments {len(segments)}, kernel_size {len(kernel_size)}, layer_type {len(layer_type)} and n {len(n)} must be the same size."
            )

        if len(channels) == len(n) + 1 is False:
            raise ValueError(
                f"Length of channels list {channels} should be one more than number of layers."
            )

        layer_list = []
        for i in range(len(channels) - 1):
            if normalization is not None:
                layer_list.append(normalization)

            layer = high_order_convolution_layers(
                layer_type=layer_type[i],
                n=n[i],
                in_channels=channels[i],
                out_channels=channels[i + 1],
                kernel_size=kernel_size[i],
                segments=segments[i],
                rescale_output=rescale_output,
                periodicity=periodicity,
            )
            layer_list.append(layer)

        self.model = nn.Sequential(*layer_list)

    def forward(self, x: Tensor) -> Tensor:
        return self.model(x)


class HighOrderFullyDeconvolutionalNetwork(nn.Module):
    def __init__(
        self,
        layer_type: Union[List[str], str],
        n: List[int],
        channels: List[int],
        segments: List[int],
        kernel_size: List[int],
        rescale_output: bool = False,
        periodicity: float = None,
        normalization: Callable[[Any], Tensor] = None,
    ) -> None:
        """
        Args :

        """
        super().__init__()

        if len(channels) < 2:
            raise ValueError(
                f"Channels list must have at least 2 values [input_channels, output_channels]"
            )

        if (
            len(channels)
            == len(segments)
            == len(kernel_size)
            == len(layer_type)
            == len(n)
            is False
        ):
            raise ValueError(
                f"Lists for channels {len(channels)}, segments {len(segments)}, kernel_size {len(kernel_size)}, layer_type {len(layer_type)} and n {len(n)} must be the same size."
            )

        if len(channels) == len(n) + 1 is False:
            raise ValueError(
                f"Length of channels list {channels} should be one more than number of layers."
            )

        layer_list = []
        for i in range(len(channels) - 1):
            if normalization is not None:
                layer_list.append(normalization)

            layer = high_order_convolution_transpose_layers(
                layer_type=layer_type[i],
                n=n[i],
                in_channels=channels[i],
                out_channels=channels[i + 1],
                kernel_size=kernel_size[i],
                segments=segments[i],
                rescale_output=rescale_output,
                periodicity=periodicity,
            )
            layer_list.append(layer)

        self.model = nn.Sequential(*layer_list)

    def forward(self, x: Tensor) -> Tensor:
        return self.model(x)


class VanillaVAE(nn.Module):
    def __init__(
        self,
        in_channels: int,
        latent_dim: int,
        hidden_dims: List[int],
        encoder: nn.Module,
        decoder: nn.Module,
        **kwargs,
    ) -> None:
        super(VanillaVAE, self).__init__()

        self.latent_dim = latent_dim

        self.encoder = encoder
        self.fc_mu = nn.Linear(hidden_dims[-1] * 4, latent_dim)
        self.fc_var = nn.Linear(hidden_dims[-1] * 4, latent_dim)

        self.decoder_input = nn.Linear(latent_dim, hidden_dims[-1] * 4)
        self.decoder = decoder

    def encode(self, input: Tensor) -> List[Tensor]:
        """
        Encodes the input by passing through the encoder network
        and returns the latent codes.
        :param input: (Tensor) Input tensor to encoder [N x C x H x W]
        :return: (Tensor) List of latent codes
        """
        result = self.encoder(input)
        result = torch.flatten(result, start_dim=1)

        # Split the result into mu and var components
        # of the latent Gaussian distribution
        mu = self.fc_mu(result)
        log_var = self.fc_var(result)

        return [mu, log_var]

    def decode(self, z: Tensor) -> Tensor:
        """
        Maps the given latent codes
        onto the image space.
        :param z: (Tensor) [B x D]
        :return: (Tensor) [B x C x H x W]
        """
        result = self.decoder_input(z)
        result = result.view(-1, 512, 2, 2)
        result = self.decoder(result)
        result = self.final_layer(result)
        return result

    def reparameterize(self, mu: Tensor, logvar: Tensor) -> Tensor:
        """
        Reparameterization trick to sample from N(mu, var) from
        N(0,1).
        :param mu: (Tensor) Mean of the latent Gaussian [B x D]
        :param logvar: (Tensor) Standard deviation of the latent Gaussian [B x D]
        :return: (Tensor) [B x D]
        """
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return eps * std + mu

    def forward(self, input: Tensor, **kwargs) -> List[Tensor]:
        mu, log_var = self.encode(input)
        z = self.reparameterize(mu, log_var)
        return [self.decode(z), input, mu, log_var]

    def loss_function(self, *args, **kwargs) -> dict:
        """
        Computes the VAE loss function.
        KL(N(\mu, \sigma), N(0, 1)) = \log \frac{1}{\sigma} + \frac{\sigma^2 + \mu^2}{2} - \frac{1}{2}
        :param args:
        :param kwargs:
        :return:
        """
        recons = args[0]
        input = args[1]
        mu = args[2]
        log_var = args[3]

        kld_weight = kwargs["M_N"]  # Account for the minibatch samples from the dataset
        recons_loss = F.mse_loss(recons, input)

        kld_loss = torch.mean(
            -0.5 * torch.sum(1 + log_var - mu ** 2 - log_var.exp(), dim=1), dim=0
        )

        loss = recons_loss + kld_weight * kld_loss
        return {
            "loss": loss,
            "Reconstruction_Loss": recons_loss.detach(),
            "KLD": -kld_loss.detach(),
        }

    def sample(self, num_samples: int, current_device: int, **kwargs) -> Tensor:
        """
        Samples from the latent space and return the corresponding
        image space map.
        :param num_samples: (Int) Number of samples
        :param current_device: (Int) Device to run the model
        :return: (Tensor)
        """
        z = torch.randn(num_samples, self.latent_dim)

        z = z.to(current_device)

        samples = self.decode(z)
        return samples

    def generate(self, x: Tensor, **kwargs) -> Tensor:
        """
        Given an input image x, returns the reconstructed image
        :param x: (Tensor) [B x C x H x W]
        :return: (Tensor) [B x C x H x W]
        """

        return self.forward(x)[0]


class HighOrderMLPMixerBlock(nn.Module):
    # Follow this block https://papers.nips.cc/paper/2021/file/cba0a4ee5ccd02fda0fe3f9a3e7b89fe-Paper.pdf
    pass


def interpolate_high_order_mlp(network_in: HighOrderMLP, network_out: HighOrderMLP):
    """
    Create a new network with weights interpolated from network_in.  If network_out has higher
    polynomial order than network_in then the output network will produce identical results to
    the input network, but be of higher polynomial order.  At this point the output network can
    be trained given the lower order network for weight initialization.  This technique is known
    as p-refinement (polynomial-refinement).

    Args :
        network_in : The starting network with some polynomial order n
        network_out : The output network.  This network should be initialized however its weights
        will be overwritten with interpolations from network_in
    """
    layers_in = [
        module
        for module in network_in.model.modules()
        if not isinstance(module, nn.Sequential)
    ]
    layers_out = [
        module
        for module in network_out.model.modules()
        if not isinstance(module, nn.Sequential)
    ]

    layer_pairs = zip(layers_in, layers_out)

    for l_in, l_out in layer_pairs:
        interpolate_polynomial_layer(l_in, l_out)
