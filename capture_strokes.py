import pygame
import numpy as np
import os
from handwriting_synthesis.config import style_path

class StrokeCapture:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        
        # Window setup
        self.width = 800
        self.height = 300
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Handwriting Capture")
        
        # Colors
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.GRAY = (200, 200, 200)
        
        # Font
        self.font = pygame.font.SysFont('Arial', 20)
        
        # Drawing variables
        self.strokes = []  # List to store all strokes
        self.current_stroke = []  # Current stroke points
        self.drawing = False
        
        # Text input
        self.sample_text = "The quick brown fox jumps over the lazy dog"
        
        # Buttons
        self.clear_button = pygame.Rect(10, self.height - 40, 100, 30)
        self.save_button = pygame.Rect(120, self.height - 40, 100, 30)

    def draw_screen(self):
        self.screen.fill(self.WHITE)
        
        # Draw text area
        text_surface = self.font.render(f"Text: {self.sample_text}", True, self.BLACK)
        self.screen.blit(text_surface, (10, 10))
        
        # Draw guidelines
        pygame.draw.line(self.screen, self.GRAY, (0, 150), (self.width, 150), 1)  # baseline
        pygame.draw.line(self.screen, self.GRAY, (0, 100), (self.width, 100), 1)  # midline
        
        # Draw all completed strokes
        for stroke in self.strokes:
            if len(stroke) > 1:
                pygame.draw.lines(self.screen, self.BLACK, False, stroke, 2)
        
        # Draw current stroke
        if len(self.current_stroke) > 1:
            pygame.draw.lines(self.screen, self.BLACK, False, self.current_stroke, 2)
        
        # Draw buttons
        pygame.draw.rect(self.screen, self.GRAY, self.clear_button)
        pygame.draw.rect(self.screen, self.GRAY, self.save_button)
        
        clear_text = self.font.render("Clear", True, self.BLACK)
        save_text = self.font.render("Save", True, self.BLACK)
        
        self.screen.blit(clear_text, (self.clear_button.x + 25, self.clear_button.y + 5))
        self.screen.blit(save_text, (self.save_button.x + 30, self.save_button.y + 5))
        
        pygame.display.flip()

    def save_strokes(self):
        if not self.strokes:
            print("Warning: No strokes to save!")
            return
            
        # Convert to the required format: [x_offset, y_offset, end_stroke_flag]
        formatted_strokes = []
        
        for stroke in self.strokes:
            if len(stroke) < 2:  # Skip strokes with less than 2 points
                continue
            
            stroke = np.array(stroke)
            # Calculate offsets between consecutive points
            offsets = np.diff(stroke, axis=0)
            
            if len(offsets) > 0:  # Only process if we have valid offsets
                # Add end_stroke_flag (0 for within stroke, 1 for end of stroke)
                flags = np.zeros(len(offsets))
                flags[-1] = 1  # Mark end of stroke
                
                # Combine offsets and flags
                stroke_data = np.column_stack((offsets, flags))
                formatted_strokes.extend(stroke_data)
        
        if not formatted_strokes:  # Check if we have any valid strokes after processing
            print("Warning: No valid strokes to save! Make sure to draw complete strokes.")
            return
            
        formatted_strokes = np.array(formatted_strokes)
        
        # Create style directory if it doesn't exist
        os.makedirs(style_path, exist_ok=True)
        
        # Find next available style number
        style_num = 0
        while os.path.exists(f"{style_path}/style-{style_num}-strokes.npy"):
            style_num += 1
            
        # Save in the style format
        np.save(f"{style_path}/style-{style_num}-strokes.npy", formatted_strokes)
        np.save(f"{style_path}/style-{style_num}-chars.npy", self.sample_text.encode())
        
        print(f"Success! Saved as style-{style_num}\nStrokes shape: {formatted_strokes.shape}")
        self.strokes = []
        self.current_stroke = []

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # Check if clicked on buttons
                    if self.clear_button.collidepoint(event.pos):
                        self.strokes = []
                        self.current_stroke = []
                    elif self.save_button.collidepoint(event.pos):
                        self.save_strokes()
                    else:
                        self.drawing = True
                        self.current_stroke = [event.pos]
                
                elif event.type == pygame.MOUSEBUTTONUP:
                    if self.drawing and self.current_stroke:
                        self.strokes.append(self.current_stroke)
                        self.current_stroke = []
                    self.drawing = False
                
                elif event.type == pygame.MOUSEMOTION and self.drawing:
                    self.current_stroke.append(event.pos)
            
            self.draw_screen()
        
        pygame.quit()

if __name__ == "__main__":
    capture = StrokeCapture()
    capture.run() 