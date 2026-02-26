import pygame


class StatusBar:
    def __init__(self, x, y, w, h, label, font):
        self.rect = pygame.Rect(x, y, w, h)
        self.label = label
        self.font = font
        self.bg_color = (44, 62, 80)      # Sophisticated dark blue-gray
        self.border_color = (189, 195, 199) # Light gray border
        self.radius = 8

    def draw(self, screen, value):
        # Draw background container
        pygame.draw.rect(screen, self.bg_color, self.rect, border_radius=self.radius)
        
        # Determine bar color
        if self.label == 'Stress':
            # Red if high stress
            bar_color = (231, 76, 60) if value > 70 else (46, 204, 113)
        else:
            # Red if low status (e.g. caffeine/energy)
            bar_color = (231, 76, 60) if value < 30 else (46, 204, 113)

        # Draw fill
        fill_width = int(self.rect.width * value / 100)
        if fill_width > 0:
            fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_width, self.rect.height)
            pygame.draw.rect(screen, bar_color, fill_rect, border_radius=self.radius)

        # Draw border
        pygame.draw.rect(screen, self.border_color, self.rect, 2, border_radius=self.radius)

        # Draw label
        text = self.font.render(f"{self.label}: {int(value)}", True, (236, 240, 241))
        screen.blit(text, (self.rect.x, self.rect.y - 28))


class Button:
    def __init__(self, x, y, w, h, text, font, enabled=True):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.font = font
        self.enabled = enabled
        self.base_color = (52, 152, 219)    # Bright blue
        self.hover_color = (41, 128, 185)   # Darker blue
        self.disabled_color = (127, 140, 141) # Gray
        self.border_color = (236, 240, 241) # Off-white
        self.radius = 10

    def draw(self, screen):
        mouse_pos = pygame.mouse.get_pos()
        is_hovered = self.rect.collidepoint(mouse_pos)

        if not self.enabled:
            color = self.disabled_color
            txt_color = (189, 195, 199)
        elif is_hovered:
            color = self.hover_color
            txt_color = (255, 255, 255)
        else:
            color = self.base_color
            txt_color = (255, 255, 255)

        # Draw main button
        pygame.draw.rect(screen, color, self.rect, border_radius=self.radius)
        # Draw border
        pygame.draw.rect(screen, self.border_color, self.rect, 2, border_radius=self.radius)

        txt = self.font.render(self.text, True, txt_color)
        screen.blit(txt, txt.get_rect(center=self.rect.center))

    def clicked(self, event):
        return (
            self.enabled
            and event.type == pygame.MOUSEBUTTONDOWN
            and self.rect.collidepoint(event.pos)
        )


def _hours_to_hhmm(hours: float) -> str:
    total_minutes = round(hours * 60)
    h = total_minutes // 60
    m = total_minutes % 60
    return f"{h}:{m:02d}"


class InputBox:
    # Field indices
    FIELD_H = 0
    FIELD_M = 1

    def __init__(self, font, smallfont):
        self.font = font
        self.smallfont = smallfont
        self.prompt_text = ""
        self.active = False
        self._h_text = ""        # hours digits (up to 2)
        self._m_text = ""        # minutes digits (exactly 2)
        self._focus = self.FIELD_H   # which field is active
        self.result = None
        self._action_name = ""
        self.max_hours = 99.0
        self._error = ""


    def open(self, action_name, max_hours: float = 99.0):
        self.active = True
        self._h_text = ""
        self._m_text = ""
        self._focus = self.FIELD_H
        self.result = None
        self._error = ""
        self._action_name = action_name
        self.max_hours = max_hours
        max_str = _hours_to_hhmm(max_hours)
        self.prompt_text = f"How long? (max {max_str})"


    def _total_hours(self) -> float | None:
        if not self._h_text:
            return None
        h = int(self._h_text)
        m = int(self._m_text) if self._m_text else 0
        if m >= 60:
            return None
        return h + m / 60.0


    def handle_event(self, event):
        if not self.active:
            return None

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.active = False
                self._error = ""
                return None

            if event.key == pygame.K_RETURN:
                return self._try_confirm()

            if event.key == pygame.K_BACKSPACE:
                self._error = ""
                if self._focus == self.FIELD_H:
                    self._h_text = self._h_text[:-1]
                else:
                    if self._m_text:
                        self._m_text = self._m_text[:-1]
                    else:
                        # backspace from empty minutes → jump back to hours
                        self._focus = self.FIELD_H

            elif event.key == pygame.K_TAB:
                # Toggle between fields
                self._focus = self.FIELD_M if self._focus == self.FIELD_H else self.FIELD_H
                self._error = ""

            elif event.unicode.isdigit():
                self._error = ""
                self._type_digit(event.unicode)
        
        if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                
                if self.h_rect.collidepoint(mouse_pos):
                    self._focus = self.FIELD_H
                    self._error = ""
                
                elif self.m_rect.collidepoint(mouse_pos):
                    self._focus = self.FIELD_M
                    self._error = ""
        return None

    def _type_digit(self, ch: str):
        if self._focus == self.FIELD_H:
            if len(self._h_text) < 2:
                self._h_text += ch
                # Auto-jump: if we already have 2 hour digits, move to minutes
                if len(self._h_text) == 2:
                    self._focus = self.FIELD_M
        else:
            if len(self._m_text) < 2:
                self._m_text += ch
        return None

    def _try_confirm(self):
        value = self._total_hours()
        if value is None or value <= 0:
            self._error = "Enter a valid time greater than 0"
            return None
        m = int(self._m_text) if self._m_text else 0
        if m >= 60:
            self._error = "Minutes must be 0-59"
            return None
        if value > self.max_hours + 1e-9:
            self._error = f"Max allowed: {_hours_to_hhmm(self.max_hours)}"
            return None
        self.result = value
        self.active = False
        self._error = ""
        return self.result


    def draw(self, screen):
        if not self.active:
            return

        # Semi-transparent overlay
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        box_w, box_h = 360, 170
        box_x = (screen.get_width() - box_w) // 2
        box_y = (screen.get_height() - box_h) // 2
        box_rect = pygame.Rect(box_x, box_y, box_w, box_h)

        pygame.draw.rect(screen, (40, 40, 60), box_rect, border_radius=10)
        pygame.draw.rect(screen, (255, 255, 255), box_rect, 2, border_radius=10)

        # Prompt
        prompt_surf = self.font.render(self.prompt_text, True, (255, 255, 255))
        screen.blit(prompt_surf, (box_x + 20, box_y + 18))

        # Two input fields
        field_y = box_y + 58
        field_h = 44

        # Hours field
        self.h_rect = pygame.Rect(box_x + 20, field_y, 110, field_h)
        h_active = self._focus == self.FIELD_H
        h_border_color = (255, 220, 80) if h_active else (140, 140, 200)
        pygame.draw.rect(screen, (55, 55, 80), self.h_rect, border_radius=6)
        pygame.draw.rect(screen, h_border_color, self.h_rect, 2, border_radius=6)

        if not self._h_text:
            # Placeholder
            ph = self.font.render("HH", True, (100, 100, 130))
            screen.blit(ph, ph.get_rect(center=self.h_rect.center))
        else:
            h_surf = self.font.render(self._h_text, True, (255, 255, 255))
            screen.blit(h_surf, h_surf.get_rect(center=self.h_rect.center))

        # Colon separator
        colon_surf = self.font.render(":", True, (200, 200, 200))
        colon_x = box_x + 20 + 110 + 10
        screen.blit(colon_surf, colon_surf.get_rect(centery=field_y + field_h // 2, x=colon_x))

        # Minutes field
        self.m_rect = pygame.Rect(colon_x + 22, field_y, 110, field_h)
        m_active = self._focus == self.FIELD_M
        m_border_color = (255, 220, 80) if m_active else (140, 140, 200)
        pygame.draw.rect(screen, (55, 55, 80), self.m_rect, border_radius=6)
        pygame.draw.rect(screen, m_border_color, self.m_rect, 2, border_radius=6)

        if not self._m_text:
            ph = self.font.render("MM", True, (100, 100, 130))
            screen.blit(ph, ph.get_rect(center=self.m_rect.center))
        else:
            m_surf = self.font.render(self._m_text, True, (255, 255, 255))
            screen.blit(m_surf, m_surf.get_rect(center=self.m_rect.center))

        # Labels under fields
        h_lbl = self.font.render("Hours", True, (160, 160, 200))
        screen.blit(h_lbl, h_lbl.get_rect(centerx=self.h_rect.centerx, y=field_y + field_h + 4))
        m_lbl = self.font.render("Minutes", True, (160, 160, 200))
        screen.blit(m_lbl, m_lbl.get_rect(centerx=self.m_rect.centerx, y=field_y + field_h + 4))

        # Error or hint
        if self._error:
            err_surf = self.font.render(self._error, True, (255, 100, 100))
            screen.blit(err_surf, (box_x + 20, box_y + 140))
        else:
            hint = "Tab to switch field    Enter to confirm    Esc to cancel"
            hint_surf = self.smallfont.render(hint, True, (140, 140, 180))
            screen.blit(hint_surf, (box_x + 20, box_y + 140))


class NumberBox:
    def __init__(self, font, smallfont):
        self.font = font
        self.smallfont = smallfont
        self.active = False
        self.prompt_text = ""
        self._text = ""
        self.result = None
        self._error = ""
        self._max = 999

    def open(self, prompt: str, max_value: int = 999):
        self.active = True
        self._text = ""
        self.result = None
        self._error = ""
        self._max = max_value
        self.prompt_text = prompt

    def handle_event(self, event):
        if not self.active:
            return None
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.active = False
                self._error = ""
                return None
            elif event.key == pygame.K_RETURN:
                if not self._text:
                    self._error = "Enter a number first"
                    return None
                val = int(self._text)
                if val <= 0:
                    self._error = "Must be at least 1"
                elif val > self._max:
                    self._error = f"Max is {self._max}"
                else:
                    self.result = val
                    self.active = False
                    self._error = ""
                    return self.result
            elif event.key == pygame.K_BACKSPACE:
                self._text = self._text[:-1]
                self._error = ""
            elif event.unicode.isdigit() and len(self._text) < 3:
                self._text += event.unicode
                self._error = ""
        return None

    def draw(self, screen):
        if not self.active:
            return
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        box_w, box_h = 360, 150
        box_x = (screen.get_width() - box_w) // 2
        box_y = (screen.get_height() - box_h) // 2
        box_rect = pygame.Rect(box_x, box_y, box_w, box_h)

        pygame.draw.rect(screen, (40, 40, 60), box_rect, border_radius=10)
        pygame.draw.rect(screen, (255, 255, 255), box_rect, 2, border_radius=10)

        prompt_surf = self.font.render(self.prompt_text, True, (255, 255, 255))
        screen.blit(prompt_surf, (box_x + 20, box_y + 18))

        field_rect = pygame.Rect(box_x + 20, box_y + 58, box_w - 40, 44)
        pygame.draw.rect(screen, (55, 55, 80), field_rect, border_radius=6)
        pygame.draw.rect(screen, (255, 220, 80), field_rect, 2, border_radius=6)

        if self._text:
            val_surf = self.font.render(self._text, True, (255, 255, 255))
            screen.blit(val_surf, val_surf.get_rect(center=field_rect.center))
        else:
            ph = self.font.render("0", True, (100, 100, 130))
            screen.blit(ph, ph.get_rect(center=field_rect.center))

        if self._error:
            err_surf = self.font.render(self._error, True, (255, 100, 100))
            screen.blit(err_surf, (box_x + 20, box_y + 112))
        else:
            hint_surf = self.smallfont.render("Enter to confirm    Esc to cancel", True, (140, 140, 180))
            screen.blit(hint_surf, (box_x + 20, box_y + 118))


class AlertBox:
    def __init__(self, font, smallfont):
        self.font = font
        self.smallfont = smallfont
        self.active = False
        self.title = ""
        self.body = ""

    def open(self, title: str, body: str):
        self.active = True
        self.title = title
        self.body = body

    def handle_event(self, event):
        if not self.active:
            return None
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.active = False
                return True
        if event.type == pygame.MOUSEBUTTONDOWN:
            if hasattr(self, '_btn_rect') and self._btn_rect.collidepoint(event.pos):
                self.active = False
                return True
        return None

    def draw(self, screen):
        if not self.active:
            return

        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        box_w, box_h = 420, 200
        box_x = (screen.get_width() - box_w) // 2
        box_y = (screen.get_height() - box_h) // 2
        box_rect = pygame.Rect(box_x, box_y, box_w, box_h)

        pygame.draw.rect(screen, (60, 20, 20), box_rect, border_radius=10)
        pygame.draw.rect(screen, (255, 80, 80), box_rect, 2, border_radius=10)

        # Title
        title_surf = self.font.render(self.title, True, (255, 80, 80))
        screen.blit(title_surf, title_surf.get_rect(centerx=box_rect.centerx, y=box_y + 18))

        # Body  (wrap at ~50 chars manually if needed)
        body_surf = self.smallfont.render(self.body, True, (220, 220, 220))
        screen.blit(body_surf, body_surf.get_rect(centerx=box_rect.centerx, y=box_y + 58))

        # Continue button
        btn_w, btn_h = 120, 36
        self._btn_rect = pygame.Rect(
            box_rect.centerx - btn_w // 2,
            box_y + box_h - btn_h - 16,
            btn_w, btn_h
        )
        pygame.draw.rect(screen, (180, 40, 40), self._btn_rect, border_radius=6)
        pygame.draw.rect(screen, (255, 120, 120), self._btn_rect, 2, border_radius=6)
        btn_surf = self.smallfont.render("Continue  [Enter]", True, (255, 255, 255))
        screen.blit(btn_surf, btn_surf.get_rect(center=self._btn_rect.center))
