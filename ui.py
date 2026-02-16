import pygame

class StatusBar:
    def __init__(self, x, y, w, h, label, font):
        self.rect = pygame.Rect(x, y, w, h)
        self.label = label
        self.font = font

    def draw(self, screen, value):
        pygame.draw.rect(screen, (50, 50, 50), self.rect)

        fill_width = int(self.rect.width * value / 100)
        fill_rect = pygame.Rect(
            self.rect.x, self.rect.y, fill_width, self.rect.height
        )
        pygame.draw.rect(screen, (0, 180, 0), fill_rect)

        pygame.draw.rect(screen, (255, 255, 255), self.rect, 2)

        text = self.font.render(f"{self.label}: {int(value)}", True, (255, 255, 255))
        screen.blit(text, (self.rect.x, self.rect.y - 26))


class Button:
    def __init__(self, x, y, w, h, text, font, enabled=True):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.font = font
        self.enabled = enabled

    def draw(self, screen):
        if self.enabled:
            pygame.draw.rect(screen, (70, 70, 200), self.rect)
            pygame.draw.rect(screen, (255, 255, 255), self.rect, 2)
            txt_color = (255, 255, 255)
        else:
            pygame.draw.rect(screen, (100, 100, 100), self.rect) 
            pygame.draw.rect(screen, (150, 150, 150), self.rect, 2)
            txt_color = (180, 180, 180)


        txt = self.font.render(self.text, True, txt_color)
        screen.blit(txt, txt.get_rect(center=self.rect.center))

    def clicked(self, event):
        return (
            self.enabled
            and event.type == pygame.MOUSEBUTTONDOWN
            and self.rect.collidepoint(event.pos)
        )


class InputBox:
    """Overlay prompt that asks the player to enter a number of hours."""

    def __init__(self, font):
        self.font = font
        self.prompt_text = ""
        self.active = False
        self.text = ""
        self.result = None          # filled when user presses Enter
        self._action_name = ""      # which action triggered the prompt
        self.max_hours = 99

    def open(self, action_name, max_hours=99):
        self.active = True
        self.text = ""
        self.result = None
        self._action_name = action_name
        self.max_hours = max_hours
        self.prompt_text = f"Enter hours (1-{max_hours}):"

    def handle_event(self, event):
        """Process keyboard input. Returns the entered int on Enter, or None."""
        if not self.active:
            return None
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                if self.text and 0 < int(self.text) <= self.max_hours:
                    self.result = int(self.text)
                    self.active = False
                    return self.result
            elif event.key == pygame.K_ESCAPE:
                self.active = False
                self.text = ""
                return None
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.unicode.isdigit() and len(self.text) < 2:
                self.text += event.unicode
        return None

    def draw(self, screen):
        if not self.active:
            return
        # Semi-transparent overlay
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        box_w, box_h = 340, 140
        box_x = (screen.get_width() - box_w) // 2
        box_y = (screen.get_height() - box_h) // 2
        box_rect = pygame.Rect(box_x, box_y, box_w, box_h)

        pygame.draw.rect(screen, (40, 40, 60), box_rect, border_radius=10)
        pygame.draw.rect(screen, (255, 255, 255), box_rect, 2, border_radius=10)

        prompt_surf = self.font.render(self.prompt_text, True, (255, 255, 255))
        screen.blit(prompt_surf, (box_x + 20, box_y + 20))

        # Input field
        input_rect = pygame.Rect(box_x + 20, box_y + 60, box_w - 40, 36)
        pygame.draw.rect(screen, (70, 70, 90), input_rect, border_radius=5)
        pygame.draw.rect(screen, (180, 180, 255), input_rect, 2, border_radius=5)
        input_surf = self.font.render(self.text, True, (255, 255, 255))
        screen.blit(input_surf, (input_rect.x + 10, input_rect.y + 6))

        hint_surf = self.font.render("Press Enter to confirm, Esc to cancel", True, (180, 180, 180))
        screen.blit(hint_surf, (box_x + 20, box_y + 106))
