import pygame
pygame.init()

def check(font, factor, r):
	distance = [0]
	for i in range(*r):
		size = factor*i
		f = pygame.freetype.Font(font, size)
		surf = f.render("helloHello", "#FFFFFF")[0]
		if surf.get_height() != i:
			distance.append(surf.get_height()-i)
		print(f"pixel: {i}, size: {round(size)}, height: {surf.get_height()}")

	print(f"error: {len(distance)-1}, distance max: {max(distance)}")


check("font/Marker Felt.ttf", 1.14155, (1,500))
