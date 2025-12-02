
import os
from transformers import AutoModelForCausalLM, AutoTokenizer, TextDataset, DataCollatorForLanguageModeling, Trainer, TrainingArguments

def train_chatbot():
    model_name = "microsoft/DialoGPT-medium"
    dataset_path = "movie_dataset.txt"
    output_dir = "./trained_chatbot"

    # Ensure the output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name)

    # Add a padding token if it doesn't exist
    if tokenizer.pad_token is None:
        tokenizer.add_special_tokens({'pad_token': tokenizer.eos_token})
        model.resize_token_embeddings(len(tokenizer))

    train_dataset = TextDataset(
        tokenizer=tokenizer,
        file_path=dataset_path,
        block_size=128  # Adjust block size based on your data and memory
    )

    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False
    )

    training_args = TrainingArguments(
        output_dir=output_dir,
        overwrite_output_dir=True,
        num_train_epochs=3,  # Adjust number of epochs
        per_device_train_batch_size=4,  # Adjust batch size based on your GPU memory
        save_steps=10_000,
        save_total_limit=2,
        logging_dir='./logs',
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        data_collator=data_collator,
        train_dataset=train_dataset,
    )

    print("Starting model training...")
    trainer.train()
    print("Training complete.")

    # Save the fine-tuned model and tokenizer
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"Model saved to {output_dir}")

if __name__ == "__main__":
    train_chatbot()
