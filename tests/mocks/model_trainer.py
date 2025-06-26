"""
Mock implementation of the model trainer for testing.
"""
class ModelTrainer:
    """Mock model trainer that doesn't require PyTorch."""
    
    def __init__(self, *args, **kwargs):
        self.model = None
        self.tokenizer = None
        self.device = 'cpu'
    
    def train(self, *args, **kwargs):
        return {'train_runtime': 0.0, 'train_samples_per_second': 0.0}
    
    def save_model(self, *args, **kwargs):
        pass
    
    @classmethod
    def from_pretrained(cls, *args, **kwargs):
        return cls()

# Create a mock version of the model trainer module
mock_module = type('ModelTrainerModule', (), {
    'ModelTrainer': ModelTrainer,
})
