# Black-Litterman model views

from typing import List

class View:
	view_type: str # 'absolute' or 'relative'
	value: float # expected return or expected outperformance
	confidence: float # confidence level in the view
	
	def __init__(self, yaml_dict, view_type):
		self.view_type = view_type
		self.confidence = yaml_dict['confidence']
		if (view_type == "absolute"):
			self.value = yaml_dict['expected_return']
		elif (view_type == "relative"):
			self.value = yaml_dict['expected_outperformance']
		else:
			raise ValueError("Invalid view type")

class RelativeView(View):
	long: List[str]
	short: List[str]

	def __init__(self, yaml_dict):
		super().__init__(yaml_dict, "relative")
		self.long = flat_str_list(yaml_dict['long'])
		self.short = flat_str_list(yaml_dict['short'])

class AbsoluteView(View):
	assets: List[str]
	
	def __init__(self, yaml_dict):
		super().__init__(yaml_dict, "absolute")
		self.assets = flat_str_list(yaml_dict['asset'])


def flat_str_list(s: str | List[str]) -> str:
	"""
	Helper function to ensure a string or list of strings is returned as a flat list of strings.
	"s" -> ["s"]
	["s1", "s2"] -> ["s1", "s2"]
	"""
	return [s] if isinstance(s, str) else s