# ui.py
import pygame

class StatusBar:
    def __init__(self, x, y, w, h, label):
        self.rect = pygame.Rect(x, y, w, h)
        self.label = label
        self.font = pygame.font.SysFont(None, 22)

    def draw(self, screen, value):
        pygame.draw.rect(screen, (50, 50, 50), self.rect)

        fill_width = int(self.rect.width * value / 100)
        fill_rect = pygame.Rect(
            self.rect.x, self.rect.y, fill_width, self.rect.height
        )
        pygame.draw.rect(screen, (0, 180, 0), fill_rect)

        pygame.draw.rect(screen, (255, 255, 255), self.rect, 2)

        text = self.font.render(f"{self.label}: {int(value)}", True, (255, 255, 255))
        screen.blit(text, (self.rect.x, self.rect.y - 18))


class Button:
    def __init__(self, x, y, w, h, text):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.font = pygame.font.SysFont(None, 26)

    def draw(self, screen):
        pygame.draw.rect(screen, (70, 70, 200), self.rect)
        pygame.draw.rect(screen, (255, 255, 255), self.rect, 2)

        txt = self.font.render(self.text, True, (255, 255, 255))
        screen.blit(txt, txt.get_rect(center=self.rect.center))

    def clicked(self, event):
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and self.rect.collidepoint(event.pos)
        )
