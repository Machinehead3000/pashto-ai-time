"""
Model training and fine-tuning functionality.
"""
import os
import logging
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

import torch
from torch.utils.data import Dataset, DataLoader
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)

logger = logging.getLogger(__name__)

class FineTuningDataset(Dataset):
    """Dataset for fine-tuning language models."""
    
    def __init__(self, tokenizer, file_path: str, block_size: int = 512):
        """Initialize the dataset.
        
        Args:
            tokenizer: Tokenizer to use for encoding
            file_path: Path to the training data file
            block_size: Maximum sequence length
        """
        self.tokenizer = tokenizer
        self.block_size = block_size
        
        # Load and process the dataset
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        
        # Tokenize all texts
        self.examples = []
        for text in lines:
            tokenized_text = tokenizer.encode(
                text,
                add_special_tokens=True,
                max_length=block_size,
                truncation=True
            )
            self.examples.append(tokenized_text)
    
    def __len__(self):
        return len(self.examples)
    
    def __getitem__(self, idx):
        return torch.tensor(self.examples[idx], dtype=torch.long)

class ModelTrainer:
    """Handles training and fine-tuning of language models."""
    
    def __init__(
        self,
        model_name: str = "gpt2",
        output_dir: str = "output",
        device: str = None
    ):
        """Initialize the model trainer.
        
        Args:
            model_name: Name or path of the pre-trained model
            output_dir: Directory to save the trained model
            device: Device to use for training ('cuda', 'mps', 'cpu')
        """
        self.model_name = model_name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Set device
        self.device = device or ("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
        
        # Initialize tokenizer and model
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.tokenizer.pad_token = self.tokenizer.eos_token
        
        self.model = AutoModelForCausalLM.from_pretrained(model_name).to(self.device)
    
    def prepare_dataset(self, train_file: str, val_file: str = None, block_size: int = 512) -> Tuple[Dataset, Optional[Dataset]]:
        """Prepare training and validation datasets.
        
        Args:
            train_file: Path to training data file
            val_file: Optional path to validation data file
            block_size: Maximum sequence length
            
        Returns:
            Tuple of (train_dataset, val_dataset)
        """
        train_dataset = FineTuningDataset(
            tokenizer=self.tokenizer,
            file_path=train_file,
            block_size=block_size
        )
        
        val_dataset = None
        if val_file and os.path.exists(val_file):
            val_dataset = FineTuningDataset(
                tokenizer=self.tokenizer,
                file_path=val_file,
                block_size=block_size
            )
        
        return train_dataset, val_dataset
    
    def train(
        self,
        train_dataset: Dataset,
        val_dataset: Dataset = None,
        batch_size: int = 4,
        num_epochs: int = 3,
        learning_rate: float = 5e-5,
        warmup_steps: int = 500,
        save_steps: int = 1000,
        logging_steps: int = 100,
        **training_args
    ) -> None:
        """Train the model.
        
        Args:
            train_dataset: Training dataset
            val_dataset: Optional validation dataset
            batch_size: Batch size for training
            num_epochs: Number of training epochs
            learning_rate: Learning rate
            warmup_steps: Number of warmup steps
            save_steps: Save model every X steps
            logging_steps: Log training metrics every X steps
            **training_args: Additional training arguments
        """
        # Set up training arguments
        training_args = TrainingArguments(
            output_dir=str(self.output_dir),
            overwrite_output_dir=True,
            num_train_epochs=num_epochs,
            per_device_train_batch_size=batch_size,
            per_device_eval_batch_size=batch_size,
            evaluation_strategy="steps" if val_dataset is not None else "no",
            eval_steps=save_steps,
            save_steps=save_steps,
            logging_steps=logging_steps,
            save_total_limit=2,
            load_best_model_at_end=val_dataset is not None,
            learning_rate=learning_rate,
            warmup_steps=warmup_steps,
            **training_args
        )
        
        # Set up data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False
        )
        
        # Initialize Trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            data_collator=data_collator,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
        )
        
        # Train the model
        trainer.train()
        
        # Save the final model
        trainer.save_model(str(self.output_dir))
        self.tokenizer.save_pretrained(str(self.output_dir))
        
        logger.info(f"Model training complete. Model saved to {self.output_dir}")
    
    def save_model(self, output_dir: str = None) -> None:
        """Save the trained model and tokenizer.
        
        Args:
            output_dir: Directory to save the model (defaults to the one set during init)
        """
        save_dir = Path(output_dir) if output_dir else self.output_dir
        save_dir.mkdir(parents=True, exist_ok=True)
        
        self.model.save_pretrained(str(save_dir))
        self.tokenizer.save_pretrained(str(save_dir))
        logger.info(f"Model and tokenizer saved to {save_dir}")
    
    @classmethod
    def from_pretrained(cls, model_path: str, **kwargs):
        """Load a trained model from disk.
        
        Args:
            model_path: Path to the saved model
            **kwargs: Additional arguments for the trainer
            
        Returns:
            ModelTrainer instance with loaded model
        """
        trainer = cls(model_name=model_path, **kwargs)
        trainer.model = AutoModelForCausalLM.from_pretrained(model_path).to(trainer.device)
        trainer.tokenizer = AutoTokenizer.from_pretrained(model_path)
        return trainer
