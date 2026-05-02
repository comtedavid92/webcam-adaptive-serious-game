## Model training

No analysis was performed here. The models were trained using all the data collected with the random-based DDA.

See [replay analysis](../replay_analysis/) for more information about the models and the training data.

The models are stored in `.pkl` format :

```python
import cloudpickle

path_to_model = ...

with open(path_to_model, "rb") as file:
    data = cloudpickle.load(file)
    model = data["model"]
    scaler = data["scaler"]
```

And are available here : [pretrained models](2026-03-29-18-15-41/).