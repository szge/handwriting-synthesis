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
        
        # Font
        self.font = pygame.font.SysFont('Arial', 20)
        
        # Style navigation
        self.current_style = 0
        self.max_style = self._get_max_style()
        
        # Drawing variables
        self.strokes = []  # List to store all strokes
        self.current_stroke = []  # Current stroke points
        self.drawing = False
        self.drawing_mode = False  # Toggle between view/draw modes
        
        # Text input
        self.default_text = "A lazy zebra gazes at the moon"  # New default text with 'a' and 'z'
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

    def _get_max_style(self):
        style_num = 0
        while os.path.exists(f"{style_path}/style-{style_num}-strokes.npy"):
            style_num += 1
        return style_num - 1

    def load_current_style(self):
        try:
            self.strokes = []  # Clear any drawing strokes
            self.current_stroke = []
            
            loaded_strokes = np.load(f"{style_path}/style-{self.current_style}-strokes.npy")
            self.text = np.load(f"{style_path}/style-{self.current_style}-chars.npy").tostring().decode('utf-8')
            
            # Convert offsets to absolute coordinates
            coords = []
            current_pos = np.array([400, 150])  # Start at center
            
            for stroke in loaded_strokes:
                offset = np.array([stroke[0], -stroke[1]])
                current_pos = current_pos + offset
                coords.append(current_pos.copy())
                
                if stroke[2] == 1:  # End of stroke
                    coords.append(None)  # Mark stroke boundary
            
            self.coords = coords
            self.drawing_mode = False
            
        except Exception as e:
            print(f"Error loading style {self.current_style}: {e}")
            self.coords = []
            self.text = "Error loading style"

    def save_strokes(self):
        if not self.strokes:
            print("Warning: No strokes to save!")
            return
            
        formatted_strokes = []
        center_pos = np.array([400, 150])  # Same center position as in load_current_style
        last_pos = center_pos
        
        for stroke in self.strokes:
            if len(stroke) < 2:
                continue
            
            stroke = np.array(stroke)
            # Calculate offset from center for first point of stroke
            first_offset = stroke[0] - last_pos
            # Calculate offsets between consecutive points within the stroke
            point_offsets = np.diff(stroke, axis=0)
            
            # Combine first offset with point offsets
            offsets = np.vstack([first_offset, point_offsets])
            
            if len(offsets) > 0:
                # Invert y-coordinates for offsets
                offsets[:, 1] *= -1
                
                # Add end-stroke flags (0 for all except last point)
                flags = np.zeros(len(offsets))
                flags[-1] = 1
                
                stroke_data = np.column_stack((offsets, flags))
                formatted_strokes.extend(stroke_data)
            
            # Update last position for next stroke
            last_pos = stroke[-1]
        
        if not formatted_strokes:
            print("Warning: No valid strokes to save!")
            return
            
        formatted_strokes = np.array(formatted_strokes)
        
        # Save over current style
        np.save(f"{style_path}/style-{self.current_style}-strokes.npy", formatted_strokes)
        np.save(f"{style_path}/style-{self.current_style}-chars.npy", self.text.encode())
        
        print(f"Success! Saved as style-{self.current_style}\nStrokes shape: {formatted_strokes.shape}")
        self.load_current_style()  # Reload to verify

    def draw_screen(self):
        self.screen.fill(self.WHITE)
        
        # Draw style info
        info_text = f"Style {self.current_style} of {self.max_style}"
        if self.drawing_mode:
            info_text += " (Drawing Mode)"
        text_surface = self.font.render(info_text, True, self.BLACK)
        self.screen.blit(text_surface, (10, 10))
        
        # Draw sample text
        text_surface = self.font.render(f"Text: {self.text[:50]}...", True, self.BLACK)
        self.screen.blit(text_surface, (10, 40))
        
        # Draw guidelines
        pygame.draw.line(self.screen, self.GRAY, (0, 150), (self.width, 150), 1)
        pygame.draw.line(self.screen, self.GRAY, (0, 100), (self.width, 100), 1)
        
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
        self.strokes = []
        self.current_stroke = []
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
                        self.drawing = True
                        self.current_stroke = [event.pos]
                
                elif event.type == pygame.MOUSEBUTTONUP:
                    if self.drawing_mode and self.drawing and self.current_stroke:
                        self.strokes.append(self.current_stroke)
                        self.current_stroke = []
                    self.drawing = False
                
                elif event.type == pygame.MOUSEMOTION and self.drawing:
                    self.current_stroke.append(event.pos)
                
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
    tool = StyleTool()
    tool.run() 