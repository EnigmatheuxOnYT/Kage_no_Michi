#Projet : Kage no Michi
#Auteurs : Alptan Korkmaz, Maxime Rousseaux, Ahmed-Adam Rezkallah, Clément Roux--Bénabou, Cyril Zhao


# -*- coding: utf-8 -*-
"""
Created on Mon Jan 20 17:38:15 2025

@author: clementroux--benabou
"""

import pygame
import math
import random
from enum import Enum
from Cinematics import Cinematics
from map.src.game import Game_map
from Audio import Music,Sound

class minigm_collect :
    
    def __init__ (self,screen):
        ### Etats du mini-jeu ###
        
        #Si le jeu tourne
        self.running = True
        
        #Si le mini-jeu est entrain d'âtre joué
        self.playing = False
        
        #Si la phase de gameplay (entre l'intro et la fin) est active
        self.in_minigm = False
        
        ### Appel de la classe cinématique, on utilisera principalement self.cin.cinematic_frame() et self.cin.cinematics_bgs
        self.cin = Cinematics()
        self.map = Game_map(screen,load_only=[True,"mg8"])
        
        ### Appel des classes pour l'audio, on utilisera principalement la fonction play() et les variables (aller voir le fichier)
        self.music,self.sound = Music(),Sound()
        
        ### Variables ###
        self.gp_phases = Enum("Phase","BEGIN SEARCH LEAVING WIN PERFECT_WIN")
         
        self.obtained_objects = 0
        self.load_assets()
        
    ########## Démarrage du mini-jeu ##########
    def load (self):
        self.playing = True
        self.current_gp_phase = self.gp_phases.BEGIN
        self.display_arrow = False
        self.arrow_queue = []
        self.current_arrow_target = 0
        self.arrow_initiated = False

        self.map.map_manager.change_map("mg8")
        self.items_hotspots = random.sample([i for i in range(1,11)],5)
        self.display_catch_text = False
        self.hot_spots = {str(i) : {"name":f"mgm_hotspot_{i}", "found":False, 'have_item':True if i in self.items_hotspots else False} for i in range (1,11)}
        self.hot_spots["0"] = {"name":"spawn"}
        self.press_a = True
        self.on_object = [False]
        self.obtained_objects = 0
        print(self.items_hotspots)
        self.got_timer = 0
        self.task_timer = pygame.time.get_ticks()
     
    def load_assets(self):
        # Importer les images, sons etc.. ici (depuis "../data/assets")
        
        self.arrow = pygame.image.load("../data/assets/minigm/Flèche_Directionnelle_Bas.png").convert_alpha()
        self.current_arrow_rect= pygame.Rect(0,0,99,99)
        
        
        ### Importation de la police d'écriture (taille des textes des dialogues)
        self.font_MFMG30 = pygame.font.Font("../data/assets/fonts/MadouFutoMaruGothic.ttf",30)

        self.catch_text = self.font_MFMG30.render("Appuyez sur A pour ramasser", False, "red")
        self.catch_text_rect = self.set_rect(self.catch_text)
        
        object_obtained_text_placeholder = self.get_object_obtained_text()
        self.object_obtained_text_rect = self.set_rect(object_obtained_text_placeholder)
        self.display_object_obtained_text = False

    def get_object_obtained_text (self): return self.font_MFMG30.render(f"Objet obtenu ! ({self.obtained_objects}/5)", False, "black")

    def set_rect (self,text_surface:pygame.surface.Surface,pos="mb"):
        rect = text_surface.get_rect()
        if pos == "mb":
            rect.midbottom = (640,720)
        return rect
     
    ########## Intro/Fin ##########
    def intro(self,screen,saved):
        #Appeler ici la fonction self.cin.cinematic_frame()
        #Exemple d'utilisation que vous pouvez copier coller (attention, TOUJOURS finir l'appel par running=self.running):
        
        self.cin.cinematic_frame(screen,'mgm1',running=self.running)
        
        #À la toute fin de la fonction
        self.in_minigm = True
        self.current_gp_phase = self.gp_phases.SEARCH
    
    def leave(self,screen,saved):
        self.current_gp_phase = self.gp_phases.SEARCH
    
    def end(self,screen,saved):
        #Appeler ici la fonction self.cin.cinematic_frame()
        if self.current_gp_phase == self.gp_phases.PERFECT_WIN:
            pass
        elif self.current_gp_phase == self.gp_phases.WIN:
            pass
        
        #À la toute fin de la fonction
        self.playing = False
        
    ########## Partie 1 : évènements ##########
    def minigm_events (self):
        #Poser les évènements vérifiés dans la suite de la boucle for
        for event in pygame.event.get():
            #Vérification de la fermeture du jeu
            if event.type == pygame.QUIT:
                self.running = False
                pygame.event.post(event)
        
        
        #Vérification des touches appuyées
        pressed_keys = pygame.key.get_pressed()
        
        #Vérification de la muise en plein écran
        if pressed_keys[pygame.K_F11]: 
            pygame.display.toggle_fullscreen()
            pygame.time.Clock().tick(5)
        elif self.on_object[0] and pressed_keys[pygame.K_a]:
            if not self.press_a:
                self.catch()
            else:
                self.press_a = False
                
        self.map.player.save_location()
        self.map.handle_input(self.running,from_game=True)
    
    def catch (self):
        obj_num = self.on_object[1]
        self.hot_spots[str(obj_num)]['found'] = True
        self.got_timer = pygame.time.get_ticks()
        self.display_object_obtained_text = True
        if obj_num in self.items_hotspots :
            self.obtained_objects += 1
            if self.arrow_get_busy():
                for i in self.arrow_queue:
                        if i == obj_num:
                            self.arrow_queue.remove(i)
        else:
            loop=True
            for i in self.items_hotspots:
                if i not in self.arrow_queue and not self.hot_spots[str(i)]["found"] and loop:
                    self.arrow_queue.append(i)
                    self.arrow_initiated = True
                    loop=False
            
    
    ########## Partie 2 : Mise à jour ##########
    def minigm_update (self):
        
        if self.current_gp_phase == self.gp_phases.SEARCH:
            self.on_object = [False]
            self.map.update()
            events=self.map.map_manager.get_current_active_events()
            self.handle_zone_events(events)
            if self.arrow_get_busy() and self.arrow_initiated:
                self.current_arrow_target = self.arrow_queue[0]
                self.arrow_update(self.hot_spots[str(self.current_arrow_target)]['name'])
            self.display_arrow = self.arrow_get_busy()
        elif self.current_gp_phase == self.gp_phases.LEAVING:
            pass
        elif self.current_gp_phase in [self.gp_phases.WIN,self.gp_phases.PERFECT_WIN]:
            self.in_minigm = False
    
    def handle_zone_events (self,events):
        for i in range(len(events)):
            event = events[i]
            data = event.data
            
            if event.type == "mgm_leave":
                if self.current_gp_phase == self.gp_phases.SEARCH:
                    self.current_gp_phase = self.gp_phases.LEAVING
            
            if event.type == "mgm_hotspot":
                if self.current_gp_phase == self.gp_phases.SEARCH:
                    if  not self.hot_spots[str(data[0])]["found"]:
                        self.on_object = [True,data[0]]
    
    def arrow_update (self,point=None,coordinates=None):
        screen_rect = self.map.map_manager.get_map().group._map_layer.view_rect
        if coordinates==None:
            if point==None:
                target_point=[0,0]
            else:
                target_point = self.map.map_manager.get_point_pos(point)
        elif point==None:
            target_point=coordinates
        player_pos = self.map.map_manager.player.rect
        
        diffs = [(target_point[0]-player_pos.centerx),(target_point[1]-player_pos.centery)]
        if diffs[0]==0 and diffs[1]==0:
            angle = 0
        else:
            hypotenuse = math.sqrt((diffs[0]**2)+(diffs[1]**2))
            angle = math.degrees(math.asin(diffs[0]/hypotenuse))
        if diffs[1]<0:
            angle=-angle+180
            
        self.current_arrow_surface = pygame.transform.rotate(self.arrow,angle)
        
        self.current_arrow_rect.top = (player_pos.bottom-screen_rect.top)*2+5
        self.current_arrow_rect.left = (player_pos.left-screen_rect.left)*2+5
    
    def arrow_get_busy (self):return False if len(self.arrow_queue) == 0 else True
    
    
    ########## Partie 3 : Affichage ##########
    def minigm_draw (self,screen,saved):
        
        #Affichage, utiliser principalement la fonction screen.blit([surface à afficher],[ractangle dans lequel afficher la surface])
        if self.current_gp_phase == self.gp_phases.SEARCH:
            #Remplissage avec du noir (fond)
            screen.fill((0,0,0))
            self.map.map_manager.draw()
            if self.on_object[0]:
                screen.blit(self.catch_text,self.catch_text_rect)
            elif self.display_object_obtained_text:
                if pygame.time.get_ticks()-self.got_timer <1000:
                    alpha_value = ((500-pygame.time.get_ticks()+self.got_timer)*255/100)
                    object_obtained_text = self.get_object_obtained_text()
                    object_obtained_text.set_alpha(alpha_value)
                    screen.blit(object_obtained_text,self.object_obtained_text_rect)
                else:
                    self.display_object_obtained_text = False
            if self.display_arrow and self.arrow_initiated:
                screen.blit(self.current_arrow_surface,self.current_arrow_rect)
        elif self.current_gp_phase == self.gp_phases.LEAVING:
            self.leave(screen,saved)
        
        #Mise à jour de l'écran
        pygame.display.flip()
    
   
    ########## Boucle mini-jeu ##########
    def run (self,screen,saved):
        #L'argument saved permet de savoir quelle version de l'intro et de la fin afficher en fonction de qui a été sauvé. Il permet aussi d'afficher le bon sprite dans le mini-jeu le cas échéant 
        
        self.load()
        self.intro(screen,saved)
        
        while self.playing and self.running and self.in_minigm:
            self.minigm_events()
            self.minigm_update()
            self.minigm_draw(screen,saved)
            pygame.time.Clock().tick(60)
            
        if self.playing and self.running:
            self.end(screen,saved)
        
        return self.running

#Lancement du mini-jeu
if __name__ == '__main__':
    pygame.init()
    
    icon = pygame.image.load("../data/assets/common/Icone_LOGO_V12.ico")
    pygame.display.set_icon(icon)
    cursor = pygame.image.load("../data/assets/common/Souris_V4.png")
    pygame.mouse.set_cursor((5,5),cursor)
    screen = pygame.display.set_mode((1280,720))
    pygame.display.set_caption("Kage no michi")
    
    minigm = minigm_collect(screen)
    minigm.run(screen, 'KM')
    pygame.quit()
    
