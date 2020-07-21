from bindsnet.network import Network
from bindsnet.pipeline import EnvironmentPipeline
from bindsnet.learning import MSTDP
from bindsnet.encoding import bernoulli
from bindsnet.network.topology import Connection
from bindsnet.environment import GymEnvironment
from bindsnet.network.nodes import Input, LIFNodes
from bindsnet.pipeline.action import select_softmax

import torch

# Build network.
network = Network(dt=1.0)
if torch.cuda.is_available():
    device = "cuda:0"
else:
    device = "cpu"
torch.cuda.set_device(device)
# network.to(dev)
# Layers of neurons.
inpt = Input(n=80 * 80, shape=[1, 1, 1, 80, 80], traces=True)
# inpt.to(dev)
middle = LIFNodes(n=100, traces=True)
# middle.to(dev)
out = LIFNodes(n=4, refrac=0, traces=True)
# out.to(dev)

# Connections between layers.
inpt_middle = Connection(source=inpt, target=middle, wmin=0, wmax=1e-1)
# inpt_middle.to(dev)
middle_out = Connection(
    source=middle,
    target=out,
    wmin=0,
    wmax=1,
    update_rule=MSTDP,
    nu=1e-1,
    norm=0.5 * middle.n,
)
# middle_out.to(dev)

# Add all layers and connections to the network.
network.add_layer(inpt, name="Input Layer")
network.add_layer(middle, name="Hidden Layer")
network.add_layer(out, name="Output Layer")
network.add_connection(inpt_middle, source="Input Layer", target="Hidden Layer")
network.add_connection(middle_out, source="Hidden Layer", target="Output Layer")

network.to(device)

# Load the Breakout environment.
environment = GymEnvironment("BreakoutDeterministic-v4")
environment.reset()

# Build pipeline from specified components.
environment_pipeline = EnvironmentPipeline(
    network,
    environment,
    encoding=bernoulli,
    action_function=select_softmax,
    output="Output Layer",
    time=100,
    history_length=1,
    delta=1,
    plot_interval=1,
    render_interval=1,
    # device=dev,
)


def run_pipeline(pipeline, episode_count):
    for i in range(episode_count):
        total_reward = 0
        pipeline.reset_state_variables()
        is_done = False
        while not is_done:
            result = pipeline.env_step()
            pipeline.step(result)

            reward = result[1]
            total_reward += reward

            is_done = result[2]
        print(f"Episode {i} total reward:{total_reward}")

print("Training: ")
run_pipeline(environment_pipeline, episode_count=100)

# stop MSTDP
environment_pipeline.network.learning = False

print("Testing: ")
run_pipeline(environment_pipeline, episode_count=100)
