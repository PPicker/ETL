import pandas as pd
from torch import no_grad
from transformers import AutoProcessor, AutoModel
from PIL import Image
from typing import List
import torch

class Embedding_Model():
    def __init__(self, model_name='Marqo/marqo-fashionCLIP'):
        self.model_name = model_name
        self.processor = AutoProcessor.from_pretrained(model_name, trust_remote_code=True)
        self.model = AutoModel.from_pretrained(model_name, trust_remote_code=True)
        self.dim = 512

    @torch.inference_mode
    def embed_images(self, all_images):
        # 한 번에 이미지 임베딩 계산 (배치 처리)
        inputs = self.processor(images=all_images, return_tensors="pt", padding=True)
        with no_grad():
            return self.model.get_image_features(**inputs,normalize=True)
    @torch.inference_mode
    def embed_image(self, image):
        inputs = self.processor(images=image, return_tensors="pt")
        with no_grad():
            image_features = self.model.get_image_features(**inputs,normalize=True)
        return image_features.squeeze(0)  # 배치 차원 제거

    # 텍스트 임베딩 함수
    @torch.inference_mode
    def embed_text(self, text, max_length=77):
        inputs = self.processor(
            text=[text], 
            return_tensors="pt", 
            truncation=True, 
            padding='max_length', 
            max_length=max_length
        )
        with no_grad():
            text_features = self.model.get_text_features(**inputs,normalize=True)
        return text_features.squeeze(0)
if __name__ == '__main__':
    model = Embedding_Model()
    model.embed_text('hi')