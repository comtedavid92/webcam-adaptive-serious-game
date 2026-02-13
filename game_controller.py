import pygame
import time


class _GameBackground:

    COLOR = 0
    IMAGE = 1

    _BACKGROUNDS = [
        COLOR,
        IMAGE,
    ]

    @staticmethod
    def get_backgrounds():
        return _GameBackground._BACKGROUNDS
    
    @staticmethod
    def create_background_color(color):
        obj = _GameBackground(_GameBackground.COLOR)
        obj.color = color
        return obj

    @staticmethod
    def create_background_image(image):
        obj = _GameBackground(_GameBackground.IMAGE)
        obj.image = image
        return obj
    
    def __init__(self, type):
        self.type = type
        self.color = None
        self.image = None

    def draw(self, surface):
        if self.type == _GameBackground.COLOR:
            # Fill the surface
            surface.fill(self.color)
        elif self.type == _GameBackground.IMAGE:
            # Copy the image to the surface
            # Axes swap : source image is [height, width], Pygame expects [width, height]
            pygame.surfarray.blit_array(surface, self.image.swapaxes(0, 1))


class _GameObject:

    CIRCLE = 0
    LINE   = 1
    TEXT   = 2

    _OBJECTS = [
        CIRCLE,
        LINE,
        TEXT,
    ]

    @staticmethod
    def get_objects():
        return _GameObject._OBJECTS

    @staticmethod
    def create_object_circle(x, y, color, radius):
        obj = _GameObject(_GameObject.CIRCLE)
        obj.x1 = x
        obj.y1 = y
        obj.color = color
        obj.radius = radius
        return obj

    @staticmethod
    def create_object_line(x1, y1, x2, y2, color, width):
        obj = _GameObject(_GameObject.LINE)
        obj.x1 = x1
        obj.y1 = y1
        obj.x2 = x2
        obj.y2 = y2
        obj.color = color
        obj.width = width
        return obj

    @staticmethod
    def create_object_text(x, y, color, text, text_size):
        obj = _GameObject(_GameObject.TEXT)
        obj.x1 = x
        obj.y1 = y
        obj.color = color
        obj.text = text
        obj.text_size = text_size
        return obj

    def __init__(self, type):
        self.type = type
        self.creation_ts = time.time()
        self.x1 = 0
        self.y1 = 0
        self.x2 = 0
        self.y2 = 0
        self.color = None
        # Circle
        self.radius = 0
        # Line
        self.width = 0
        # Text
        self.text = ""
        self.text_size = 0

    def update_object_circle(self, x, y, color, radius):
        if self.type != _GameObject.CIRCLE: raise RuntimeError("The object is not a circle")
        self.x1 = x if x is not None else self.x1
        self.y1 = y if y is not None else self.y1
        self.color = color if color is not None else self.color
        self.radius = radius if radius is not None else self.radius

    def update_object_line(self, x1, y1, x2, y2, color, width):
        if self.type != _GameObject.LINE: raise RuntimeError("The object is not a line")
        self.x1 = x1 if x1 is not None else self.x1
        self.y1 = y1 if y1 is not None else self.y1
        self.x2 = x2 if x2 is not None else self.x2
        self.y2 = y2 if y2 is not None else self.y2
        self.color = color if color is not None else self.color
        self.width = width if width is not None else self.width

    def update_object_text(self, x, y, color, text, text_size):
        if self.type != _GameObject.TEXT: raise RuntimeError("The object is not a text")
        self.x1 = x if x is not None else self.x1
        self.y1 = y if y is not None else self.y1
        self.color = color if color is not None else self.color
        self.text = text if text is not None else self.text
        self.text_size = text_size if text_size is not None else self.text_size

    def draw(self, surface):
        if self.type == _GameObject.CIRCLE:
            self._draw_circle(surface)
        elif self.type == _GameObject.LINE:
            self._draw_line(surface)
        elif self.type == _GameObject.TEXT:
            self._draw_text(surface)

    def is_expired(self, max_duration_ms):
        current_ts = time.time()
        duration_ms = (current_ts - self.creation_ts) * 1000
        expired = duration_ms > max_duration_ms
        return expired
    
    def in_contact(self, obj):
        if self.type == _GameObject.CIRCLE and obj.type == _GameObject.CIRCLE:
            return self._in_contact_circle_with_circle(obj)
        else:
            raise RuntimeError("The contact function is not available for these objects")

    def _draw_circle(self, surface):
        pygame.draw.circle(surface, self.color, (self.x1, self.y1), self.radius)

    def _draw_line(self, surface):
        pygame.draw.line(surface, self.color, (self.x1, self.y1), (self.x2, self.y2), self.width)

    def _draw_text(self, surface):
        font = pygame.font.Font(None, self.text_size) # Default font
        text_surface = font.render(self.text, True, self.color) # Anti-aliasing enabled
        surface.blit(text_surface, (self.x1, self.y1))

    def _in_contact_circle_with_circle(self, obj):
        a = self.x1 - obj.x1
        b = self.y1 - obj.y1
        c = self.radius + obj.radius
        return a*a + b*b <= c*c


class _GameEvent:

    EXPIRED = 0
    CONTACT = 1
    DWELL   = 2

    _EVENTS = [
        EXPIRED,
        CONTACT,
        DWELL,
    ]

    @staticmethod
    def get_events():
        return _GameEvent._EVENTS
    
    @staticmethod
    def create_event_expired(object1, max_duration_ms):
        event = _GameEvent(_GameEvent.EXPIRED)
        event.object1 = object1
        event.max_duration_ms = max_duration_ms
        return event
    
    @staticmethod
    def create_event_contact(object1, object2):
        event = _GameEvent(_GameEvent.CONTACT)
        event.object1 = object1
        event.object2 = object2
        return event
    
    @staticmethod
    def create_event_dwell(object1, object2, min_duration_ms):
        event = _GameEvent(_GameEvent.DWELL)
        event.object1 = object1
        event.object2 = object2
        event.min_duration_ms = min_duration_ms
        return event
    
    def __init__(self, type):
        self.type = type
        self.object1 = None
        self.object2 = None
        self.continuous_state = False
        self.prev_trigger_state = False
        self.trigger_state = False
        # Expired
        self.max_duration_ms = 0
        # Dwell
        self.min_duration_ms = 0
        self.enter_dwell_ts = 0

    def update_continuous_state(self):
        state = False
        
        if self.type == _GameEvent.EXPIRED:
            state = self._get_expired()
        elif self.type == _GameEvent.CONTACT:
            state = self._get_contact()
        elif self.type == _GameEvent.DWELL:
            state = self._get_dwell()
        
        self.continuous_state = state

    def update_state(self):
        state = self.continuous_state
        self.trigger_state = False

        # The trigger state is true only when the state changes from false to true
        if state and not self.prev_trigger_state: self.trigger_state = True
        self.prev_trigger_state = state

    def _get_expired(self):
        return self.object1.is_expired(self.max_duration_ms)

    def _get_contact(self):
        return self.object1.in_contact(self.object2)

    def _get_dwell(self):
        contact = self.object1.in_contact(self.object2)
        current_ts = time.time()
        state = False

        if contact:
            if self.enter_dwell_ts == 0: self.enter_dwell_ts = current_ts # Set timestamp
            duration_ms = (current_ts - self.enter_dwell_ts) * 1000
            state = duration_ms >= self.min_duration_ms
        else:
            self.enter_dwell_ts = 0 # Reset timestamp
        
        return state


class GameController:

    COLOR_WHITE = (255, 255, 255)
    COLOR_BLACK = (0, 0, 0)
    COLOR_RED   = (231, 76, 60)
    COLOR_GREEN = (46, 204, 113)
    COLOR_BLUE  = (52, 152, 219)

    def __init__(self, fps, canvas_width, canvas_height, name = None, icon = None):
        pygame.init()
        pygame.font.init()

        if name is not None: pygame.display.set_caption(name)
        if icon is not None:
            icon = pygame.image.load(icon)
            pygame.display.set_icon(icon)

        self._running = True
        self._clock = pygame.time.Clock()
        self._fps = fps
        self._screen = pygame.display.set_mode((canvas_width, canvas_height)) # Set the screen (user window)
        self._surface = pygame.Surface((canvas_width, canvas_height)) # Set the surface (drawing buffer)
        self._background = None
        self._transient_objects = []
        self._persistent_objects = {}
        self._events = {}

    def close(self):
        pygame.font.quit()
        pygame.quit()

    def regulate_fps(self):
        self._clock.tick(self._fps)

    def refresh_states(self):
        # Process the PyGame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._running = False

        # Proces the custom events
        for event in self._events:
            event = self._events[event]
            event.update_continuous_state()
            event.update_state()

    def refresh_screen(self):
        # Draw the background
        if self._background is not None:
            self._background.draw(self._surface)
        
        # Draw the persistent object
        for object_id in sorted(self._persistent_objects):
            obj = self._persistent_objects[object_id]
            obj.draw(self._surface)

        # Draw the transient objects
        for obj in self._transient_objects:
            obj.draw(self._surface)

        # Delete the transient objects
        self._transient_objects.clear()

        # Display the screen
        self._screen.blit(self._surface, (0, 0)) # Copy the surface to the screen
        pygame.display.flip() # Display the screen
    
    def set_background_color(self, color):
        self._background = _GameBackground.create_background_color(color)
    
    def set_background_image(self, image):
        self._background = _GameBackground.create_background_image(image)

    def create_object_circle(self, object_id, x, y, color, radius):
        obj = _GameObject.create_object_circle(x, y, color, radius)
        self._add_in_transient_or_persistent_objects(object_id, obj)

    def create_object_line(self, object_id, x1, y1, x2, y2, color, width):
        obj = _GameObject.create_object_line(x1, y1, x2, y2, color, width)
        self._add_in_transient_or_persistent_objects(object_id, obj)

    def create_object_text(self, object_id, x, y, color, text, text_size):
        obj = _GameObject.create_object_text(x, y, color, text, text_size)
        self._add_in_transient_or_persistent_objects(object_id, obj)

    def update_object_circle(self, object_id, x, y, color, radius):
        obj = self._get_object(object_id)
        obj.update_object_circle(x, y, color, radius)

    def update_object_line(self, object_id, x1, y1, x2, y2, color, width):
        obj = self._get_object(object_id)
        obj.update_object_line(x1, y1, x2, y2, color, width)

    def update_object_text(self, object_id, x, y, color, text, text_size):
        obj = self._get_object(object_id)
        obj.update_object_text(x, y, color, text, text_size)

    def delete_object(self, object_id):
        self._persistent_objects.pop(object_id, None) # Avoid key error

    def create_event_expired(self, event_id, object_id, max_duration_ms):
        obj = self._get_object(object_id)
        event = _GameEvent.create_event_expired(obj, max_duration_ms)
        self._events[event_id] = event

    def create_event_contact(self, event_id, object_id1, object_id2):
        obj1 = self._get_object(object_id1)
        obj2 = self._get_object(object_id2)
        event = _GameEvent.create_event_contact(obj1, obj2)
        self._events[event_id] = event

    def create_event_dwell(self, event_id, object_id1, object_id2, min_duration_ms):
        obj1 = self._get_object(object_id1)
        obj2 = self._get_object(object_id2)
        event = _GameEvent.create_event_dwell(obj1, obj2, min_duration_ms)
        self._events[event_id] = event

    def delete_event(self, event_id):
        self._events.pop(event_id, None) # Avoid key error

    def get_running_state(self):
        return self._running
    
    def get_event_continuous_state(self, event_id):
        event = self._events.get(event_id)
        if event is None: raise RuntimeError("The event id does not exist")
        return event.continuous_state

    def get_event_state(self, event_id):
        event = self._events.get(event_id)
        if event is None: raise RuntimeError("The event id does not exist")
        return event.trigger_state
    
    def get_event_expired_remaining_time_ms(self, event_id):
        event = self._events.get(event_id)
        if event is None: raise RuntimeError("The event id does not exist")
        if event.type != _GameEvent.EXPIRED: raise RuntimeError("The event is not of type expired")
        current_ts = time.time()
        creation_ts = event.object1.creation_ts
        duration_ms = (current_ts - creation_ts) * 1000
        max_duration_ms = event.max_duration_ms
        remaining_time_ms = max(0, max_duration_ms - duration_ms)
        return remaining_time_ms
    
    def get_event_dwell_remaining_time_ms(self, event_id):
        event = self._events.get(event_id)
        if event is None: raise RuntimeError("The event id does not exist")
        if event.type != _GameEvent.DWELL: raise RuntimeError("The event is not of type dwell")
        
        current_ts = time.time()
        remaining_time_ms = 0
        
        if event.enter_dwell_ts == 0:
            remaining_time_ms = event.min_duration_ms
        else:
            duration_ms = (current_ts - event.enter_dwell_ts) * 1000
            remaining_time_ms = max(0, event.min_duration_ms - duration_ms)
        
        return remaining_time_ms

    def _add_in_transient_or_persistent_objects(self, object_id, obj):
        if object_id is None: self._transient_objects.append(obj)
        else: self._persistent_objects[object_id] = obj

    def _get_object(self, object_id):
        obj = self._persistent_objects.get(object_id)
        if obj is None: raise RuntimeError("The object id does not exist")
        return obj