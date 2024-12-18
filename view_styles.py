import pygame
import numpy as np
import os
from handwriting_synthesis.config import style_path

class StyleViewer:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        
        # Window setup
        self.width = 800
        self.height = 400
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Style Viewer")
        
        # Colors
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.GRAY = (200, 200, 200)
        self.BLUE = (0, 0, 255)
        
        # Font
        self.font = pygame.font.SysFont('Arial', 20)
        
        # Style navigation
        self.current_style = 0
        self.max_style = self._get_max_style()
        
        # Load initial style
        self.load_current_style()
        
        # Buttons
        self.prev_button = pygame.Rect(10, self.height - 40, 100, 30)
        self.next_button = pygame.Rect(120, self.height - 40, 100, 30)
        self.delete_button = pygame.Rect(230, self.height - 40, 100, 30)

    def _get_max_style(self):
        style_num = 0
        while os.path.exists(f"{style_path}/style-{style_num}-strokes.npy"):
            style_num += 1
        return style_num - 1

    def load_current_style(self):
        try:
            self.strokes = np.load(f"{style_path}/style-{self.current_style}-strokes.npy")
            self.text = np.load(f"{style_path}/style-{self.current_style}-chars.npy").tostring().decode('utf-8')
            
            # Convert offsets to absolute coordinates
            coords = []
            current_pos = np.array([400, 150])  # Start at center
            
            for stroke in self.strokes:
                # Flip the y offset (multiply by -1)
                offset = np.array([stroke[0], -stroke[1]])
                current_pos = current_pos + offset
                coords.append(current_pos.copy())
                
                if stroke[2] == 1:  # End of stroke
                    coords.append(None)  # Mark stroke boundary
            
            self.coords = coords
            
        except Exception as e:
            print(f"Error loading style {self.current_style}: {e}")
            self.coords = []
            self.text = "Error loading style"

    def draw_screen(self):
        self.screen.fill(self.WHITE)
        
        # Draw style info
        info_text = f"Style {self.current_style} of {self.max_style}"
        text_surface = self.font.render(info_text, True, self.BLACK)
        self.screen.blit(text_surface, (10, 10))
        
        # Draw sample text
        text_surface = self.font.render(f"Text: {self.text[:50]}...", True, self.BLACK)
        self.screen.blit(text_surface, (10, 40))
        
        # Draw guidelines
        pygame.draw.line(self.screen, self.GRAY, (0, 150), (self.width, 150), 1)
        pygame.draw.line(self.screen, self.GRAY, (0, 100), (self.width, 100), 1)
        
        # Draw strokes
        current_stroke = []
        for coord in self.coords:
            if coord is None:  # End of stroke
                if len(current_stroke) > 1:
                    pygame.draw.lines(self.screen, self.BLACK, False, current_stroke, 2)
                current_stroke = []
            else:
                current_stroke.append(coord)
        
        # Draw buttons
        pygame.draw.rect(self.screen, self.GRAY, self.prev_button)
        pygame.draw.rect(self.screen, self.GRAY, self.next_button)
        pygame.draw.rect(self.screen, self.GRAY, self.delete_button)
        
        prev_text = self.font.render("Previous", True, self.BLACK)
        next_text = self.font.render("Next", True, self.BLACK)
        delete_text = self.font.render("Delete", True, self.BLACK)
        
        self.screen.blit(prev_text, (self.prev_button.x + 10, self.prev_button.y + 5))
        self.screen.blit(next_text, (self.next_button.x + 30, self.next_button.y + 5))
        self.screen.blit(delete_text, (self.delete_button.x + 20, self.delete_button.y + 5))
        
        pygame.display.flip()

    def delete_current_style(self):
        try:
            os.remove(f"{style_path}/style-{self.current_style}-strokes.npy")
            os.remove(f"{style_path}/style-{self.current_style}-chars.npy")
            print(f"Deleted style {self.current_style}")
            
            # Refresh max style count and load next available style
            self.max_style = self._get_max_style()
            if self.current_style > self.max_style:
                self.current_style = self.max_style
            self.load_current_style()
            
        except Exception as e:
            print(f"Error deleting style {self.current_style}: {e}")

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.prev_button.collidepoint(event.pos):
                        if self.current_style > 0:
                            self.current_style -= 1
                            self.load_current_style()
                    
                    elif self.next_button.collidepoint(event.pos):
                        if self.current_style < self.max_style:
                            self.current_style += 1
                            self.load_current_style()
                    
                    elif self.delete_button.collidepoint(event.pos):
                        self.delete_current_style()
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        if self.current_style > 0:
                            self.current_style -= 1
                            self.load_current_style()
                    elif event.key == pygame.K_RIGHT:
                        if self.current_style < self.max_style:
                            self.current_style += 1
                            self.load_current_style()
            
            self.draw_screen()
        
        pygame.quit()

if __name__ == "__main__":
    viewer = StyleViewer()
    viewer.run() 