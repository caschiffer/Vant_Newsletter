# -*- coding: utf-8 -*-
"""
Created on Tue Jun 18 12:49:11 2019

@author: julia.gray
"""

import requests
import datetime
import get_documents



#model : pubmed or web (larger/more complex)

def get_ner_models():
	ner_models = {"bc5cdr": {"ents": ['CHEMICAL', 'DISEASE']},
				"craft": {"ents": ["GGP", "SO", "TAXON", "CHEBI", "GO", "CL"]}, 
				"bionlp13cg": {"ents": ["CANCER", "ORGAN", "TISSUE", "ORGANISM", "CELL", "AMINO_ACID", "GENE_OR_GENE_PRODUCT", "SIMPLE_CHEMICAL", "ANATOMICAL_SYSTEM", "IMMATERIAL_ANATOMICAL_ENTITY", "MULTI-TISSUE_STRUCTURE",  "DEVELOPING_ANATOMICAL_STRUCTURE", "ORGANISM_SUBDIVISION","CELLULAR_COMPONENT","ORGANISM_SUBSTANCE", "PATHOLOGICAL_FORMATION"]}, 
				"jnlpba" : {"ents": ["DNA", "CELL_TYPE", "CELL_LINE", "RNA", "PROTEIN"]},
				"pubmed" : {"ents": ["ENTITY"]}
				}
	
	label_tags = {'DISEASE':'indication_tag', 'CHEMICAL':'chemical_tag', 'GGP':'target_tag', 'SO':'target_tag', 'TAXON':'org_tag', 'CHEBI':'chemical_tag',
				   'GO':'target_tag', 'CL':'target_tag', 'CANCER':'indication_tag', 'ORGAN':'org_tag', 'TISSUE':'org_tag', 'ORGANISM':'org_tag', 'CELL':'org_tag',
				   'AMINO_ACID':'org_tag', 'GENE_OR_GENE_PRODUCT':'target_tag', 'SIMPLE_CHEMICAL':'chemical_tag', 'ANATOMICAL_SYSTEM':'org_tag', 'IMMATERIAL_ANATOMICAL_ENTITY':'org_tag',
				    'MULTI-TISSUE_STRUCTURE':'org_tag',  'DEVELOPING_ANATOMICAL_STRUCTURE':'org_tag', 'ORGANISM_SUBDIVISION':'org_tag','CELLULAR_COMPONENT':'org_tag', 'ORGANISM_SUBSTANCE':'org_tag', 'PATHOLOGICAL_FORMATION':'indication_tag',
					'DNA':'target_tag', 'CELL_TYPE':'org_tag', 'CELL_LINE':'org_tag', 'RNA':'target_tag', 'PROTEIN':'target_tag',
					'ENTITY':'org_tag'}
	
	return ner_models, label_tags

def ner_from_text(input_text, model="bc5cdr"):
	t0 = datetime.datetime.now()
	
	URL = "http://nlp.vant.com/ner/" + model
	PARAMS = {"text":input_text}

	r = requests.post(url=URL, data=PARAMS)
	#print(r)
	data = r.json()
	
	tf = datetime.datetime.now()
	print('NER EXEC TIME %s'%(str(tf-t0)))
	return data



def highlight_entities(text, entity_list, label_tags):
	offset = 0
	
	for entity in entity_list:
		span_tag = "<span class='tag_span %s' data-entity='%s'>"%(label_tags[entity['label']], entity['label'])
		entity_text = text[entity['start']+offset:entity['end']+offset]
		text = text[:entity['start']+offset] + span_tag + text[entity['start']+offset:entity['end']+offset] + '</span>' + text[entity['end']+offset:]
		entity['entity_text'] = entity_text
		offset += (len(span_tag) + len('</span>'))
		
		
		
	return text


#doc_path = "streetaccount!!!2019-06-17!!!streetaccount_37379_2019-06-17.html".replace("!!!", "/")
#solr_results = get_documents.get_solr_results_from_path('', doc_path)
#ner_models, label_tags = get_ner_models()
#ner_data = ner_from_text(solr_results['document_text'])
#highlighted_text = highlight_entities(ner_data['text'], ner_data['ents'], label_tags)


#test_doc = """http://ome.vant.com/test-app_ome/curate_ome_alert_document_v2/Press%20releases!!!html!!!01-06-2019!!!Bessor%20Pharma%20LLC_PR20_01-06-2019.html"""
#test_text = """BioSpace Movers and Shakers, May 31 | BioSpace Skip to main content --> --> Home News Jobs Job alerts Career Resources Hotbeds Career events Company Profiles Biotech Bay Biotech Beach BioCapital BioMidwest BioIndiana Bio NC BioForest Genetown Ideal Employer Pharm Country NextGen Bio Filter News BioSpace Movers and Shakers, May 31 Published: May 31, 2019 By Alex Keown Gilead Sciences California-based Gilead poached Bristol-Myers Squibb executive Johanna Mercier to serve as its new chief commercial officer. Mercier will assume responsibility for the company's commercial operations effective July 1. Laura Hamill, the current head of worldwide commercial operations, will be departing from Gilead, the company said. Mercier has held leadership positions in therapeutic areas including oncology, inflammation and neuroscience. At BMS she most recently served as president and head of the company's Large Markets division, which includes the United States, France, Germany and Japan. Mercier is a director on the Robert Wood Johnson University Hospital Board. Atara Biotherapeutics Pascal Touchon was named president and chief executive officer of South San Francisco-based Atara Therapeutics. Touchon will also serve on the company's board of directors. Touchon most recently served as global head of cell & gene at Novartis Oncology and was also a member of the Oncology Executive Committee. Previously at Novartis, Touchon served as global head of strategy, business development for oncology where he was responsible for various activities including early commercial strategy, portfolio management, business development and external collaborations. Prior Novartis, Touchon held leadership roles in research, marketing, general management and business development at various companies including Servier, Sanofi and GlaxoSmithKline. In connection with Touchon's appointment, Isaac Ciechanover stepped down from his role as president and CEO. Ciechanover will serve as a special advisor to a subcommittee of the board. Ciechanover announced plans to step down earlier this year. Sanofi -- Dietmar Berger will take over the head of development at Sanofi. The company announced Berger's appointment on Twitter. Berger most recently served as global head of research and development at South San Francisco-based Atara Biotherapeutics. According to the tweet, Berger will oversee Sanofi's clinical portfolio across all therapeutic areas and helping us bring transformative new medicines to patients. Red Hill Biopharma Israel-based Red Hill named June Almenoff as the company's first chief scientific officer. This is a new position at Red Hill. Almenoff will oversee the clinical development of RHB-204 for pulmonary nontuberculous mycobacteria (NTM) infections and the pivotal Phase III study planned to be initiated in the second half of 2019. Almenoff most recently served as president and chief medical officer of Furiex Pharmaceuticals, which was acquired by Allergan. Prior to Furiex, Almenoff worked at GlaxoSmithKline where she held various positions of increasing responsibility. Flagship Pioneering The Cambridge, Mass.-based life sciences innovation enterprise expanded its executive partner team with new leaders dedicated to its growth-stage companies. Flagship's new executive partners are Robert Berendes, Ron Hovsepian, Theo Melas Kyriazi and John Mendlein. Berendes joined Flagship Pioneering in 2014 as an advisory partner. He serves on the boards of Flagship companies focused on innovations. At Syngenta, Berendes was head of business development and a member of the executive committee, and also responsible for research and development. Hovsepian is currently chairman of Ansys and board member of Pegasystems. He recently served as president and CEO of Intralinks. Previously, he served as president and CEO of Novell. Melas-Kyriazi is a longtime member of the Flagship ecosystem. He currently serves on the board of Evelo Biosciences and was previously on the board of Moderna. Prior to joining Flagship as executive partner, Theo was chief financial officer of Levitronix Technologies. Mendlein is a longtime member of Flagship's ecosystem. He has served in multiple leadership roles at Flagship companies, including CEO of Adnexus and was a board member and the president of Moderna. He serves on the boards of new platform companies Cogen Immune Medicine and Ohana Biosciences. SQZ Biotech -- Isaac Ciechanover, former CEO of Atara Biotherapeutics, joined the board of directors of Watertown, Mass.-based SQZ Biotechnologies. Prior to his time at Atara, he worked as a partner in the life sciences practice at Kleiner Perkins Caufield & Byers and earlier, at Celgene as both an executive director for business development and a global project leader for the company's first clinical-stage biologic therapy. Ciechanover has held business development and venture capital roles at Amylin Pharmaceuticals, Pequot Ventures' healthcare practice and Pfizer. ReForm Biologics Woburn, Mass.-based ReForm Biologics added two members to its Scientific Advisory Board. ReForm named Coherus Biosciences CSO of Coherus Biosciences Alan Herman and Fred Larimore, principal consultant at Sierra Vista Biotech Consulting, to the SAB. Kintai Therapeutics Flagship Pioneering company Kintai Therapeutics formed its SAB. Board members are: Isaac Chiu, an assistant professor at Harvard Medical School in the Department of Immunology; Wendy Garrett, a professor of Immunology and Infectious Diseases at Harvard, co-director of the Harvard Chan Center for the Microbiome in Public Health, and a medical oncologist at Dana-Farber Cancer Institute; Vijay Kuchroo, the Samuel L. Wasserstrom professor of neurology at Harvard Medical School, senior scientist at Brigham and Women's Hospital and co-director of the Center for Infection and Immunity, Brigham Research Institutes; Gerald Nepom, the director of the Immune Tolerance Network and former director and founder of the Benaroya Research Institute in Seattle; Luke O'Neill, the chair of Biochemistry at Trinity College Dublin where he leads the Inflammation Research Group; and Fiona Powrie, the director of the Kennedy Institute of Rheumatology, a basic and translational inflammatory sciences center at the University of Oxford. Inventiva France-based Inventiva named Nawal Ouzren and Heinz Maeusli to the company's board of directors. Ouzren has been CEO of Sensorion since 2017. She started her career at Baxter, where she was Strategy and Operational Excellence Manager, Quality Operations director and senior director Strategy before becoming vice president of the biosimilars business unit. Maeusli served as CFO of Advanced Accelerator Applications until the company was acquired by Novartis last year. eTheRNA immunotherapies NV -- The mRNA immunotherapy company named Ulrich Platte as its new CFO. He has held progressively senior positions in financial management roles, including previous CFO roles. Platte has been engaged in a number of early-stage companies in the life science sector supporting financing and business development activities. NervGen Pharma Corp. Vancouver-based NervGen appointed Denis Bosc, as the company's vice president of chemistry, manufacturing and control (CMC). Bosc joins NervGen from the Centre for Probe Development and Commercialization, a Canadian center of excellence for commercialization and research, where he was director of Radiopharmaceutical Development and Supply. Prior to CPDC, Bosc was head of R&D at Impopharma. In addition to Bosc, long-time pharma veteran Paul Brennan has joined the NervGen team to advise on strategy and business development. Amarin Corporation -- Gwen Fisher joined Amarin Corporation in a newly created role as vice president of corporate communications. Fisher will be responsible for leading internal and external communications for the company. Specifically, she is charged with advancing and implementing an integrated, progressive corporate communications strategy designed to educate key stakeholders about the company and its lead product, Vascepa. Fisher served in a variety of leadership positions with Shire, Pfizer, Wyeth and Merck. Her last position with Shire as head of Global Portfolio Communications. Back to news --> --> Back to top For more information About Us Contact Us Terms & Conditions Privacy Policy RSS Feeds Contributors Jobs Free eNewsletters Contributors Post a job with us Hotbeds Connect with us 1985 - 2019 BioSpace.com. All rights reserved. Powered by Madgex Job Board Software"""
#smaller_test_text = """Gilead Sciences California-based Gilead poached Bristol-Myers Squibb executive Johanna Mercier to serve as its new chief commercial officer. Mercier will assume responsibility for the company's commercial operations effective July 1. Laura Hamill, the current head of worldwide commercial operations, will be departing from Gilead, the company said. Mercier has held leadership positions in therapeutic areas including oncology, inflammation and neuroscience. At BMS she most recently served as president and head of the company's Large Markets division, which includes the United States, France, Germany and Japan. Mercier is a director on the Robert Wood Johnson University Hospital Board. Atara Biotherapeutics Pascal Touchon was named president and chief executive officer of South San Francisco-based Atara Therapeutics."""

#text_data = ner_from_text(test_text)

#highlighted_text = highlight_entities(text_data['text'], text_data['ents'])




