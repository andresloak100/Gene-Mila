## The machine this task runs on (part of the task)

This pipeline runs on a laptop, not a GPU server: Apple silicon (M-series), 24 GB of memory shared with the
operating system, no CUDA. PyTorch is installed with the `mps` backend (`torch.backends.mps.is_available()` is
true; float32 only); otherwise there is the CPU. Every script you write runs under the operator's watchdog, which
kills the whole process tree, with no chance to repair it, the moment the tree's memory passes 12 GB or the script
has run for 6 hours in total (loading, preprocessing, training and prediction). A killed script is a failed task.

Design the method and write the code to use at most 10 GB of memory at any moment and at most 3 hours in total on
this machine, and state in the plan how that estimate was made. The training file is small (tens of thousands of
cells by about 2,100 genes, sparse, under 1 GB dense in float32); what fills memory is the model's activations,
for example attention over N gene tokens at batch size B needs B x heads x N^2 floats per layer. You cannot run
torch in the sandbox where you write the code, so size the model by arithmetic before the run, use `mps` when
available and the CPU otherwise, print progress (epoch, loss, seconds elapsed) with flushing, and save predictions
as soon as a trained model exists. Code that cannot run within these limits fails the task.
