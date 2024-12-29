import pygame
import numpy as np
import os
from handwriting_synthesis.config import style_path

class StyleTool:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        
        # Window setup
        self.width = 800
        self.height = 400
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Style Tool")
        
        # Colors
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.GRAY = (200, 200, 200)
        self.BLUE = (0, 0, 255)
        self.RED = (255, 0, 0)
        
        # Font
        self.font = pygame.font.SysFont('Arial', 20)
        
        # Style navigation
        self.current_style = 0
        self.max_style = self._get_max_style()
        
        # Drawing variables
        self.drawing_scale = 2.0
        self.writing_area = pygame.Rect(50, 100, 700, 200)  # Increased width from 300 to 700
        self.strokes = []
        self.current_stroke = []
        self.drawing = False
        self.drawing_mode = False
        self.max_points = 1200  # Maximum number of points allowed
        self.current_points = 0  # Counter for current points
        
        # Text input
        self.default_text = "Quick brown fox jumps over the lazy dog"
        self.text = self.default_text
        
        # Load initial style
        self.load_current_style()
        
        # Buttons
        button_y = self.height - 40
        self.prev_button = pygame.Rect(10, button_y, 100, 30)
        self.next_button = pygame.Rect(120, button_y, 100, 30)
        self.delete_button = pygame.Rect(230, button_y, 100, 30)
        self.draw_button = pygame.Rect(340, button_y, 100, 30)
        self.clear_button = pygame.Rect(450, button_y, 100, 30)
        self.save_button = pygame.Rect(560, button_y, 100, 30)
        self.refresh_button = pygame.Rect(670, button_y, 100, 30)
        self.new_button = pygame.Rect(670, 10, 100, 30)  # New button in top-right

        self.num_strokes = 0  # Add stroke counter

    def _get_max_style(self):
        style_num = 0
        while os.path.exists(f"{style_path}/style-{style_num}-strokes.npy"):
            style_num += 1
        return style_num - 1

    def load_current_style(self):
        try:
            self.strokes = []
            self.current_stroke = []
            
            loaded_strokes = np.load(f"{style_path}/style-{self.current_style}-strokes.npy")
            self.text = np.load(f"{style_path}/style-{self.current_style}-chars.npy").tostring().decode('utf-8')
            
            # Count the number of strokes by counting end-stroke flags (1s in third column)
            self.current_points = len(loaded_strokes)
            num_strokes = np.sum(loaded_strokes[:, 2] == 1)
            
            # Convert offsets to absolute coordinates
            coords = []
            current_pos = np.array([self.writing_area.left + 50, self.writing_area.centery])
            
            for stroke in loaded_strokes:
                offset = np.array([stroke[0], -stroke[1]]) * self.drawing_scale
                current_pos = current_pos + offset
                coords.append(current_pos.copy())
                
                if stroke[2] == 1:
                    coords.append(None)
            
            self.coords = coords
            self.num_strokes = int(num_strokes)  # Store stroke count
            self.drawing_mode = False
            
        except Exception as e:
            print(f"Error loading style {self.current_style}: {e}")
            self.coords = []
            self.text = "Error loading style"
            self.current_points = 0
            self.num_strokes = 0

    def save_strokes(self):
        if not self.strokes:
            print("Warning: No strokes to save!")
            return
            
        formatted_strokes = []
        start_pos = np.array([self.writing_area.left + 50, self.writing_area.centery])  # Start from left
        last_pos = start_pos
        
        for stroke in self.strokes:
            if len(stroke) < 2:
                continue
            
            stroke = np.array(stroke)
            first_offset = stroke[0] - last_pos
            point_offsets = np.diff(stroke, axis=0)
            
            offsets = np.vstack([first_offset, point_offsets])
            
            if len(offsets) > 0:
                offsets = offsets / self.drawing_scale
                offsets[:, 1] *= -1
                
                flags = np.zeros(len(offsets))
                flags[-1] = 1
                
                stroke_data = np.column_stack((offsets, flags))
                formatted_strokes.extend(stroke_data)
            
            last_pos = stroke[-1]
        
        if not formatted_strokes:
            print("Warning: No valid strokes to save!")
            return
            
        formatted_strokes = np.array(formatted_strokes)
        
        np.save(f"{style_path}/style-{self.current_style}-strokes.npy", formatted_strokes)
        np.save(f"{style_path}/style-{self.current_style}-chars.npy", self.text.encode())
        
        print(f"Success! Saved as style-{self.current_style}\nStrokes shape: {formatted_strokes.shape}")
        self.load_current_style()

    def draw_screen(self):
        self.screen.fill(self.WHITE)
        
        # Draw style info with point and stroke counter
        info_text = f"Style {self.current_style} of {self.max_style}"
        info_text += f" (Points: {self.current_points}, Strokes: {self.num_strokes})"
        
        text_surface = self.font.render(info_text, True, 
                                      self.RED if self.current_points >= self.max_points else self.BLACK)
        self.screen.blit(text_surface, (10, 10))
        
        # Draw writing area
        pygame.draw.rect(self.screen, self.GRAY, self.writing_area, 1)
        
        # Draw baseline and midline
        baseline_y = self.writing_area.centery
        midline_y = baseline_y - 50
        pygame.draw.line(self.screen, self.GRAY, 
                        (self.writing_area.left, baseline_y),
                        (self.writing_area.right, baseline_y), 1)
        pygame.draw.line(self.screen, self.GRAY,
                        (self.writing_area.left, midline_y),
                        (self.writing_area.right, midline_y), 1)
        
        # Draw sample text
        text_surface = self.font.render(f"Text: {self.text[:50]}", True, self.BLACK)
        self.screen.blit(text_surface, (10, 40))
        
        if self.drawing_mode:
            # Draw all completed strokes
            for stroke in self.strokes:
                if len(stroke) > 1:
                    pygame.draw.lines(self.screen, self.BLACK, False, stroke, 2)
            
            # Draw current stroke
            if len(self.current_stroke) > 1:
                pygame.draw.lines(self.screen, self.BLACK, False, self.current_stroke, 2)
        else:
            # Draw loaded style
            current_stroke = []
            for coord in self.coords:
                if coord is None:
                    if len(current_stroke) > 1:
                        pygame.draw.lines(self.screen, self.BLACK, False, current_stroke, 2)
                    current_stroke = []
                else:
                    current_stroke.append(coord)
        
        # Draw buttons
        buttons = [
            (self.prev_button, "Previous"),
            (self.next_button, "Next"),
            (self.delete_button, "Delete"),
            (self.draw_button, "Draw" if not self.drawing_mode else "View"),
            (self.clear_button, "Clear"),
            (self.save_button, "Save"),
            (self.refresh_button, "Refresh"),
            (self.new_button, "New Style")  # Add new button to list
        ]
        
        for button, text in buttons:
            pygame.draw.rect(self.screen, self.GRAY, button)
            text_surface = self.font.render(text, True, self.BLACK)
            self.screen.blit(text_surface, (button.x + 10, button.y + 5))
        
        pygame.display.flip()

    def delete_current_style(self):
        try:
            os.remove(f"{style_path}/style-{self.current_style}-strokes.npy")
            os.remove(f"{style_path}/style-{self.current_style}-chars.npy")
            print(f"Deleted style {self.current_style}")
            
            self.max_style = self._get_max_style()
            if self.current_style > self.max_style:
                self.current_style = self.max_style
            self.load_current_style()
            
        except Exception as e:
            print(f"Error deleting style {self.current_style}: {e}")

    def create_new_style(self):
        self.current_style = self.max_style + 1
        self.max_style = self.current_style
        self.clear_strokes()
        self.coords = []
        self.text = self.default_text
        self.drawing_mode = True

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
                    elif self.draw_button.collidepoint(event.pos):
                        self.drawing_mode = not self.drawing_mode
                        if not self.drawing_mode:
                            self.load_current_style()
                    elif self.clear_button.collidepoint(event.pos):
                        self.strokes = []
                        self.current_stroke = []
                    elif self.save_button.collidepoint(event.pos):
                        self.save_strokes()
                    elif self.refresh_button.collidepoint(event.pos):
                        self.load_current_style()
                    elif self.new_button.collidepoint(event.pos):
                        self.create_new_style()
                    elif self.drawing_mode:
                        # Only start drawing if click is inside writing area
                        if self.writing_area.collidepoint(event.pos):
                            self.drawing = True
                            self.current_stroke = [event.pos]
                
                elif event.type == pygame.MOUSEBUTTONUP:
                    if self.drawing_mode and self.drawing and self.current_stroke:
                        self.strokes.append(self.current_stroke)
                        self.current_stroke = []
                        self.num_strokes += 1  # Increment stroke counter
                    self.drawing = False
                
                elif event.type == pygame.MOUSEMOTION and self.drawing:
                    if self.writing_area.collidepoint(event.pos):
                        if self.current_points < self.max_points:
                            self.current_stroke.append(event.pos)
                            self.current_points += 1
                        else:
                            # End the stroke if we hit the limit
                            if self.current_stroke:
                                self.strokes.append(self.current_stroke)
                                self.current_stroke = []
                                self.num_strokes += 1
                            self.drawing = False
                
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

    def clear_strokes(self):
        self.strokes = []
        self.current_stroke = []
        self.current_points = 0
        self.num_strokes = 0  # Reset stroke counter

if __name__ == "__main__":
    tool = StyleTool()
    tool.run() 