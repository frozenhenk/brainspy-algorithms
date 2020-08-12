import torch
from bspyalgo.utils.performance import accuracy
from tqdm import trange
import numpy as np
import os


def train(model, dataloaders, epochs, criterion, optimizer, logger=None, save_dir=None, return_best_model=True, waveform_transforms=None):
    train_losses, val_losses = [], []
    min_val_loss = np.inf
    looper = trange(epochs, desc=' Initialising')
    for epoch in looper:
        running_loss = 0
        val_loss = 0
        for inputs, targets in dataloaders[0]:

            optimizer.zero_grad()
            if waveform_transforms is not None:
                inputs, targets = waveform_transforms((inputs, targets))
            predictions = model(inputs)
            if logger is not None and 'log_ios_train' in dir(logger):
                logger.log_ios_train(inputs, targets, predictions, epoch)
            loss = criterion(predictions, targets)
            if 'regularizer' in dir(model):
                loss = loss + model.regularizer()

            loss.backward()
            optimizer.step()
            running_loss += loss.item()

        train_losses.append(running_loss / len(dataloaders[0]))
        description = "Training Loss: {:.6f}.. ".format(train_losses[-1])

        if dataloaders[1] is not None and len(dataloaders[1]) > 0:
            with torch.no_grad():
                model.eval()
                for inputs, targets in dataloaders[1]:
                    if waveform_transforms is not None:
                        inputs, targets = waveform_transforms((inputs, targets))
                    predictions = model(inputs)
                    if logger is not None and 'log_ios_val' in dir(logger):
                        logger.log_ios_val(inputs, targets, predictions)
                    val_loss += criterion(predictions, targets)

            model.train()

            val_losses.append(val_loss / len(dataloaders[1]))
            description += "Test Loss: {:.6f}.. ".format(val_losses[-1])
            if save_dir is not None and val_losses[-1] < min_val_loss:
                min_val_loss = val_losses[-1]
                description += ' Saving model ...'
                torch.save(model, os.path.join(save_dir, 'best_model.pt'))
        looper.set_description(description)
        if logger is not None and 'log_val_predictions' in dir(logger):
            logger.log_performance(train_losses, val_losses, epoch)

        # TODO: Add a save instruction and a stopping criteria
        # if stopping_criteria(train_losses, val_losses):
        #     break

    torch.save(model, os.path.join(save_dir, 'model.pt'))
    if logger is not None:
        logger.close()
    if save_dir is not None and return_best_model and dataloaders[1] is not None and len(dataloaders[1]) > 0:
        model = torch.load(os.path.join(save_dir, 'best_model.pt'))
    return model, [torch.tensor(train_losses), torch.tensor(val_losses)]


# def test(model, dataset):
#     with torch.no_grad():
#         model.eval()
#         inputs, targets = dataset[:]
#         predictions = model(inputs)
#     #plot_gate('[ 0 0 0 1]', True, predictions, targets, show_plots=True)
#     return accuracy(predictions.squeeze(), targets.squeeze(), plot=None, return_node=True)
