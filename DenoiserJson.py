"""
CREATING JSON CONFIG FILE
passes list : 
	diffuse
	color
	albedo
	specular
	irradiance
	alpha

create config dictionnary from aov in exr
	from each aov in exr determine which channel it is

	define the required channel list to denoise (check that it's in exr file)

	for each aov check if it contains keywords:
		color:
			beauty
		diffuse:
			diffuse
		specular:
			specular
		albedo:
			albedo

"""


from termcolor import *
from datetime import datetime

import OpenEXR as exr
import os
import colorama
import json 
import numpy as np

colorama.init()





class DenoiseApplication():
	def __init__(self, sequence_path=None, output_path=None):

		self.program_path = os.getcwd()
		self.renderman_path = None

		self.sequence_path = sequence_path
		self.output_path = output_path 

		if (self.sequence_path == None) or (self.output_path == None):
			self.display_error_function("Impossible to get sequence path and output path")
			return
		if os.path.isdir(sequence_path)==False or os.path.isdir(output_path)==False:
			self.display_error_function("Sequence path or output path is not existing")
			return


		try:
			with open(os.path.join(os.getcwd(), "rmpath.txt"), "r") as read_file:
				self.renderman_path = read_file.read()
		except:
			self.display_error_function("Impossible to get renderman folder")
			return 
		else:
			if os.path.isdir(self.renderman_path)==False:
				self.display_error_function("Renderman folder doesn't exists")
				return
			else:
				self.display_success_function("Renderman folder loaded")




		self.config = {
			"dodgeList": ["zfiltered","zfiltered_var", "sampleCount"],
			"keywordList": {
				"albedo":["albedo"],
				"diffuse": ["diffuse", "Diffuse","normal","forward","backward","mse"],
				"specular": ["specular","Specular"],
				"color": ["beauty","subsurface","glass","Glass","transmissive"]
			}
		}


		self.required_aov = [
			"mse",
			"sampleCount",
			"albedo",
			"albedo_var",
			"albedo_mse",
			"diffuse",
			"diffuse_mse",
			"specular",
			"specular_mse",
			"zfiltered",
			"zfiltered_var",
			"normal",
			"normal_var",
			"normal_mse",
			"forward",
			"backward"
			]


		self.sequence_path = "D:/WORK/PYTHON/RMDENOISEAOV/batch/"
		self.output_path = "D:/WORK/PYTHON/RMDenoiseAOV/output"

		self.create_config_function()



	def display_error_function(self,message):
		print(colored("%s [ERROR] %s"%(str(datetime.now()),message), "red"))
	def display_notification_function(self,message):
		print(colored("%s : %s"%(str(datetime.now()),message), "magenta"))
	def display_success_function(self,message):
		print(colored("%s : %s"%(str(datetime.now()),message), "green"))



	def create_config_function(self):
		#check if the folder path exists
		if os.path.isdir(self.sequence_path) == False:
			display_error_function("Folder doesn't exist!")
			return

		#list all exr files in folder
		folder_content = os.listdir(self.sequence_path)
		self.exr_list = []

		for item in folder_content:
			if os.path.isfile(os.path.join(self.sequence_path,item)) == True:
				if os.path.splitext(item)[1] == ".exr":
					print(os.path.join(self.sequence_path, item))
					self.exr_list.append(os.path.join(self.sequence_path, item))


		#CHECK FOR EACH FILE OF THE EXR LIST THAT THERE IS REQUIRED AOVS
		self.display_notification_function("Checking AOV's in .exr files:")
		for file in self.exr_list:
			render_file = exr.InputFile(file)
			render_data = render_file.header()["channels"]

			for aov in self.required_aov:
				exr_aov = []

				#define the list of aovs contained in exr
				for element in list(render_data.keys()):
					if element.split(".")[0] not in exr_aov:
						exr_aov.append(element.split(".")[0])

				#check that all required aovs are in the exr file
				for required_aov in self.required_aov:
					if required_aov not in exr_aov:
						self.display_error_function("REQUIRED AOV MISSING :\nAOV missing : %s\nEXR file : %s"%(required_aov, file))
						return
		self.display_success_function("All required AOV's detected in render!")


		




		self.display_notification_function("Define the list of AOV to denoise in file : ")
		#LAUNCH CREATIION OF THE JSON DICTIONNARY FROM THE FIRST EXR OF THE SEQUENCE
		#define the list of aovs contained in the first exr 
		#and remove the dodge list from the aov list 
		#then create the json dictionnary
		file = self.exr_list[0]
		file_pass = exr.InputFile(file).header()["channels"]
		file_aov = []


		for aov in list(file_pass.keys()):
			if (aov.split(".")[0] not in self.config["dodgeList"]) and (aov.split(".")[0] not in file_aov):
				file_aov.append(aov.split(".")[0])
				print(aov.split(".")[0])

		self.display_notification_function("Create Json config dictionnary...\n\n\n")

		
		config_dictionnary = {}
		aux_dictionnary = {}
		added_list = []

		for key, value in self.config["keywordList"].items():
			
			keyword_list = value
			general_dictionnary = {}


			path = []
			layers = []

			for keyword in keyword_list:
				for aov in file_aov:
					#check if the keyword is contained in the aov
					if len(list(keyword)) > 3:
						if keyword in aov:
							if aov not in layers:
								layers.append(aov)

							if aov not in added_list:
								added_list.append(aov)

					#check if the keyword is equal to the aov
					else:
						if keyword == aov:
							if aov not in layers:
								layers.append(aov)

							if aov not in added_list:
								added_list.append(aov)


			general_dictionnary["paths"] = self.exr_list
			general_dictionnary["layers"] = layers

			aux_dictionnary[key] = [general_dictionnary]


		for aov in file_aov:
			if aov not in added_list:
				self.display_error_function("missed aov : %s"%aov)



		#FINISH THE DICTIONNARY WITH FINAL INFORMATIONS
		config_dictionnary["primary"] = self.exr_list
		config_dictionnary["aux"] = aux_dictionnary
		config_dictionnary["config"] = {
			"asymmetry": 0.0,
			"flow": False,
			"debug": False,
			"output-dir": self.output_path,
			"passes": [
				"alpha",
				"color",
				"specular",
				"diffuse"
			],
			"parameters": "%s/lib/denoise/20973-renderman.param"%self.renderman_path,
			"topology": "%s/lib/denoise/full_w1_5s_sym_gen2.topo"%self.renderman_path
		}

		self.display_success_function("Generation of dictionnary done")

		try:
			with open(os.path.join(self.program_path, "final_config.json"), "w") as save_config:
				json.dump(config_dictionnary, save_config, indent=4)
		except:
			self.display_error_function("Impossible to save JSON Config file")
		else:
			self.display_success_function("JSON Config file generated")



		self.display_notification_function("DENOISE FILES")
		try:
			os.system('"C:/Program Files/Pixar/RenderManProServer-25.2/bin/denoise_batch.exe" -j %s -o %s -cf'%(os.path.join(self.program_path, "final_config.json"), self.output_path))
		except:
			self.display_error_function("ERROR DURING DENOISING")
			return
		else:
			self.display_success_function("DENOISING DONE\nFiles generated")






			self.display_notification_function("\n\n\nCOMBINE EXR FUNCTION")
			render_file_list = []
			render_folder_list = []

			#print(os.listdir(self.output_path))

			for element in os.listdir(self.output_path):
				#print(os.path.join(self.output_path, element))
				if os.path.isfile(os.path.join(self.output_path,element))==True:
					render_file_list.append(os.path.join(self.output_path,element))
				elif os.path.isdir(os.path.join(self.output_path, element))==True:
					render_folder_list.append(os.path.join(self.output_path,element))


			print("\n\n\n")

			i=0
			while True:
				if os.path.isdir("%s/Output_Combined_%s"%(self.output_path, str(i)))==False:
					os.mkdir("%s/Output_Combined_%s"%(self.output_path,str(i)))
					combined_path = "%s/Output_Combined_%s"%(self.output_path,str(i))
					break
				else:
					i+=1

			for render in render_file_list:
				self.display_notification_function("CHECKING RENDER : %s"%render)
				combination_list = [render]

				for folder in render_folder_list:
					if (os.path.isfile(os.path.join(folder, os.path.basename(render)))==True) and (os.path.join(folder, os.path.basename(render)) not in combination_list):
						#print("render added %s"%os.path.join(folder, os.path.basename(render)))
						combination_list.append(os.path.join(folder, os.path.basename(render)))

				#generate the command to use the renderman script
				#C:\Program Files\Pixar\RenderManProServer-25.2\bin

				command=""
				for item in combination_list:
					command = "%s %s"%(command, item)
				


				command = '"%s/bin/exrmerge.exe" %s %s/Combined_%s'%(self.renderman_path, command, combined_path, os.path.basename(render))

				
				os.system(command)
				if os.path.isfile("%s/Combined_%s"%(combined_path, os.path.basename(render))) == False:
					self.display_error_function("Impossible to combine render : %s"%(os.path.basename(render)))
				else:
					self.display_success_function("Combined render created : %s"%(os.path.basename(render)))
			self.display_notification_function("DENOISING DONE")








	


#MANUAL LAUNCH
DenoiseApplication("D:/WORK/PYTHON/RMDENOISEAOV/batch", "D:/WORK/PYTHON/RMDENOISEAOV/output")



