# -*- coding: utf-8 -*-
"""
Created on Wed Jul 29 10:39:06 2020

@author: cody.schiffer
"""

import pandas as pd
import numpy as np

# list_writing = ['OP-687', 'solabegron', 'nivobotulinumtoxin A',
#                 'RQ-00434739', 'tolterodine', 'KPR-2579', 'TRPM8 antagonists',
#                 'solifenacin succinate', 'TRK-380', 'onabotulinumtoxinA', 'trospium',
#                 'tolterodine tartrate', 'DWJ-14051', 'abobotulinumtoxinA', 'AK-14',
#                 'REC-0438', 'fesoterodine fumarate', 'oxybutynin', 'mirabegron',
#                 'botulinum toxin', 'solifenacin tartrate', 'imidafenacin', 'vibegron',
#                 'oxybutynin hydrochloride', 'darifenacin', 'velufenacin', 'overactive bladder',
#                 'EP-1 receptor antagonists', 'propiverine hydrochloride', 'BAY-1817080',
#                 'oxybutynin patch', 'trospium chloride', 'J2H-1705', 'URO-902',
#                 'Relatox', 'LP-09', 'fesoterodine', 'macrocyclic peptides', 'estetrol + drospirenone',
#                 'PGL-2001', 'P2X4 receptor antagonist', 'nafarelin',
#                 'HSD-1 inhibitors', 'Endometriosis therapy 4',
#                 'mPGES-1 inhibitors', 'EP4 receptor antagonist',
#                 'cefoperazone sodium + sulbactam sodium', 'BAY-1158061',
#                 'dienogest', 'endometriosis', 'MT-2990', 'drospirenone + ethinylestradiol',
#                 'small molecule therapeutic', 'gestrinone', 'relugolix', 'gefapixant', 'histrelin',
#                 'cetrorelix', 'IMD-0560', 'alarelin acetate', 'VML-0501', 'NHP-07', 'buserelin acetate',
#                 'medroxyprogesterone acetate', 'leuprolide acetate', 'VAL-201', 'acolbifene + prasterone',
#                 'vilaprisan', 'elagolix', 'triptorelin acetate', 'alcolbifene + prasterone + GnRH agonist',
#                 'goserelin acetate', 'linzagolix', 'BAY-2328065', 'AMY-109', 'ozarelix', 'Quinagolide', 'NS-580',
#                 'relugolix + estradiol + norethindrone acetate', '17beta-hydroxysteroid dehydrogenase 1 inhibitors', 
#                 'SP-011', 'dual HSD inhibitors', 'axitinib + afatinib + linifanib', 'TU-2670', 'leuprorelin acetate',
#                 'BAY-1817080', 'triptorelin pamoate', 'lidocaine', 'VAL-301', 'EC-313', 'teverelix', 'SHR-7280',
#                 'fezolinetant', 'leuprorelin', 'CTX-30916','vardenafil', 'CAR peptide', 'Rho kinase (ROCK) inhibitors',
#                 'LASSBio-1824', 'MFC-2040', 'APN-01', 'treprostinil prodrug', 'ALT-001',
#                 ' pitavastatin', 'selegiline + PDE5 inhibitor', 'sildenafil citrate',
#                 'CTB-ACE2/ANG-(1-7)', 'treprostinil sodium', 'ROCK-II inhibitors', 'endothelin 1 inhibitors',
#                 'valproic acid', 'SC-0062', 'PF-06842874', 'PB-1046', 'ambrisentan', 'terpineol derivatives',
#                 'PBI-4050', 'bosentan', 'epoprostenol', 'riociguat', 'treprostinil diolamine',
#                 'small-molecule aminoacyl-tRNA synthetase inhibitors', 'reformulated/repurposed trimetazidine',
#                 'rimeporide', 'PDE5 inhibitors', 'SMURF1 inhibiting microRNA', 'KER-012', 'R-107',
#                 'repurposed enzastaurin', 'radiolabeled bevacizumab', 'macitentan + tadalafil',
#                 'NRF-2 activators', 'pulmonary arterial hypertension', 'SGC-003', 'bardoxolone methyl',
#                 'TOP-N53', 'CAM-2043', 'AV-353', 'treprostinil diolamine prodrug', 'ACE2 activators',
#                 'MGX-292', 'apabetalone', 'apelin receptor agonist', 'ky-3', 'nitric oxide', 'SUL-150', 'TPN-171',
#                 'ralinepag', 'macitentan', 'mRNA therapy', 'GS-444217', 'sirolimus', 'rodatristat ethyl',
#                 'MK-5475', 'udenafil', 'APT-102', 'beraprost', 'Treprostinil', 'ZIP-12 inhibitors', 'DDCI-01',
#                 'PDE10 inhibitors', 'zamicastat', 'sotatercept', 'MFC-1040', 'CAP-1002', 'fasudil', 'NTP-42',
#                 'GMA-301', 'CPI-211', 'MN-08', 'selexipag', 'GSK-2256098', 'sildenafil', 'tadalafil', 'tiprelestat',
#                 'tocilizumab', 'brilaroxazine hydrochloride', 'lonodelestat acetate', 'imatinib',
#                 'GPCR targeting antibodies', 'imatinib mesylate', 'tacrolimus', 'RARI-049', 'SERCA 2a gene therapy',
#                 'urotensin II antagonist', 'biased apelin receptor agonists', 'iloprost', 'CXA-10',
#                 'leukotriene B4 inhibitor', 'eNamptor', 'QCC-374', 'INV-240', 'ABX-464', 'seralutinib',
#                 'HSD-1 inhibitors', 'V3-Myoma', 'VPE-001', 'relugolix', 'vilaprisan', 'triptorelin acetate',
#                 'ulipristal', 'uterine fibroids', 'goserelin acetate', 'linzagolix',
#                 'relugolix + estradiol + norethindrone acetate', 'collagenase', 'DWJ-107J',
#                 'TU-2670', 'leuprorelin acetate', 'mifepristone', 'teverelix', 'SHR-7280',
#                 'fezolinetant', 'leuprorelin', 'CTX-30916','dexamethasone sodium phosphate', 'endonuclease modulators',
#                 'BOS-181', 'Microbion', 'nesolicaftor + posencaftor + dirocaftor',
#                 'glutathione + ascorbic acid + bicarbonate', 'ARO-ENaC', '6K-F17',
#                 'vancomycin hydrochloride', 'AV2.5T-SP183-fCFTRdeltaR', 'ORP-110', 'QBW-276',
#                 'next-generation CFTR correctors', 'AMG-430', 'nacystelyn', 'ABO-402', 'ND-11176',
#                 'GLPG-2451', 'Ockham Biotech', 'AB-569', 'CSA-13', 'posenacaftor + dirocaftor', 'ABO-401',
#                 'AZD-5634', 'tezacaftor + ivacaftor', 'BOS-857', 'CFTR CRISPR/Cas9 gene therapy',
#                 'ciprofloxacin', 'N-1785', 'VX-152', 'brevenal', 'mannitol', 'FDL-169 backup program',
#                 'CFTR gene therapy', 'PB-1046', 'OligoG CF-5/20', 'RV-94',
#                 'carbon dioxide + perfluorooctyl bromide', 'peptide analogs of short palate lung and nasal epithelial clone 1',
#                 'CFTR correctors', 'TL-102', 'exaluren sulfate', 'nedocromil',
#                 'TL-101', 'ETD-002', 'mercaptamine', 'CB-280', 'DRGT-102', 'MB-6',
#                 'BFP-002', 'SPIRO-2101', 'hypothiocyanite + bovine lactoferrin', 'ABBV-3903',
#                 'QRX-036', 'QRX-042', 'BFP-102', 'FDL-176', 'next generation mRNA therapy',
#                 'tobramycin', 'elexacaftor + tezacaftor + ivacaftor', 'Nu-8', 'ciprofloxacin hydrochloride',
#                 'Airway', 'SNSP-113', 'delF508-cystic fibrosis transmembrane conductance regulator correctors',
#                 'FDL-169', 'MKA-104', 'CAT-5571', 'cystic fibrosis therapeutic', 'N-1861', 'BIOC-11', 'KB-407',
#                 'N-6547', 'tobramycin + Fosfomycin', 'AT-100', 'Pseudomonas aeruginosa LasB elastase inhibitor',
#                 'Orynotide rhesus theta defensin-1', 'CFTR-targeting mRNA therapies',
#                 'RING E3-ligase gp78 inhibitors', 'QRX-052', 'miR-145 antisense oligonucleotide therapy',
#                 'heparin + undisclosed inhalant', 'nitric oxide', 'DRGT-56', 'deutivacaftor', 'DP-01',
#                 'cystic fibrosis transmembrane conductance regulator (CFTR) small-molecule potentiators',
#                 'macrocyclic compounds', 'ETD-001', 'TA-270', 'cyclodextrins', 'eluforsen',
#                 'sodium hypochlorite solution', 'fusidate sodium', 'ensifentrine', 'lumacaftor + ivacaftor',
#                 'Cystic fibrosis therapeutics', 'GLPG-1837', 'repurposed thymalfasin', 'acebilustat',
#                 'galicaftor', 'BI-1265162', 'RCT-223', 'ribosome modulating agents', 'dornase alfa biosimilar',
#                 'MRT-5005', 'CHF-6333', 'LAMELLASOME CF-NA', 'CFTR mRNA therapy', 'posenacaftor', 'seliciclib',
#                 'olacaftor', 'LUNAR-CF', 'BIOC-51', 'BI-1323495', 'alpha 1 proteinase inhibitor', 'cystic fibrosis',
#                 'BI-443651', 'CFTR gene editing therapy', 'FDL-169 + FDL-176', 'pravibismane',
#                 'repurposed lenabasum', 'nadolol', 'CTFR gene', 'ivacaftor', 'teicoplanin', 'N-6022',
#                 'SPIRO-2110', 'EVX-B2', 'elexacaftor + tezacaftor + deutivacaftor', 'vamorolone', 'FTX-003',
#                 'murepavadin', 'Aeruguard', 'alidornase alfa', 'ABBV-191', 'cavosonstat', 'VX-121',
#                 'IONIS-ENAC-2.5Rx', 'ABBV-119', 'NX-AS-401', 'Opal-L', 'amikacin sulfate', 'P-1055',
#                 'GLPG-2737', 'CFTR modulator', 'triclosan + tobramycin', 'trimethylangelicin', 'DRGT-76',
#                 'ENaC inhibitors', 'ORP-100', 'P-1037', 'SPIRO-2102', 'nesolicaftor', 'lonodelestat acetate',
#                 'ECP-104', 'FDL-176 backup program', 'gallium citrate', 'iclaprim', 'heparin + DNase', 'ABBV-3067',
#                 'GNR-039', 'BP-002', 'Laurel Capital', 'fenretinide', 'AP-PA02', 'Fosfomycin', '4D-710',
#                 'sodium pyruvate', 'aztreonam lysine', 'dirocaftor', 'LMS-611', 'CFTR second generation modulators',
#                 'gene therapy', 'tamoxifen citrate', 'MAG-DHA', 'meropenem', 'CFTR Delta F508 modulators',
#                 'dornase alfa', 'CRISPR/Cas9-based gene therapy', 'TVB-017']

#Overactive bladder
#list_writing = ['OP-687', 'solabegron', 'nivobotulinumtoxin A', 'RQ-00434739', 'tolterodine', 'KPR-2579', 'TRPM8 antagonists', 'solifenacin succinate', 'TRK-380', 'onabotulinumtoxinA', 'trospium', 'tolterodine tartrate', 'DWJ-14051', 'abobotulinumtoxinA', 'AK-14', 'REC-0438', 'fesoterodine fumarate', 'oxybutynin', 'mirabegron', 'botulinum toxin', 'solifenacin tartrate', 'imidafenacin', 'vibegron', 'oxybutynin hydrochloride', 'darifenacin', 'velufenacin', 'overactive bladder', 'EP-1 receptor antagonists', 'propiverine hydrochloride', 'BAY-1817080', 'oxybutynin patch', 'trospium chloride', 'J2H-1705', 'URO-902', 'Relatox', 'LP-09', 'fesoterodine']

#endometriosis
#list_writing = ['macrocyclic peptides', 'estetrol + drospirenone', 'PGL-2001', 'P2X4 receptor antagonist', 'nafarelin', 'HSD-1 inhibitors', 'Endometriosis therapy 4', 'mPGES-1 inhibitors', 'EP4 receptor antagonist', 'cefoperazone sodium + sulbactam sodium', 'BAY-1158061', 'dienogest', 'endometriosis', 'MT-2990', 'drospirenone + ethinylestradiol', 'small molecule therapeutic', 'gestrinone', 'relugolix', 'gefapixant', 'histrelin', 'cetrorelix', 'IMD-0560', 'alarelin acetate', 'VML-0501', 'NHP-07', 'buserelin acetate', 'medroxyprogesterone acetate', 'leuprolide acetate', 'VAL-201', 'acolbifene + prasterone', 'vilaprisan', 'elagolix', 'triptorelin acetate', 'alcolbifene + prasterone + GnRH agonist', 'goserelin acetate', 'linzagolix', 'BAY-2328065', 'AMY-109', 'ozarelix', 'Quinagolide', 'NS-580', 'relugolix + estradiol + norethindrone acetate', '17beta-hydroxysteroid dehydrogenase 1 inhibitors', 'SP-011', 'dual HSD inhibitors', 'axitinib + afatinib + linifanib', 'TU-2670', 'leuprorelin acetate', 'BAY-1817080', 'triptorelin pamoate', 'lidocaine', 'VAL-301', 'EC-313', 'teverelix', 'SHR-7280', 'fezolinetant', 'leuprorelin', 'CTX-30916']

#pulmonary arterial hypertension
#list_writing = ['vardenafil', 'CAR peptide', 'Rho kinase (ROCK) inhibitors', 'LASSBio-1824', 'MFC-2040', 'APN-01', 'treprostinil prodrug', 'ALT-001', ' pitavastatin', 'selegiline + PDE5 inhibitor', 'sildenafil citrate', 'CTB-ACE2/ANG-(1-7)', 'treprostinil sodium', 'ROCK-II inhibitors', 'endothelin 1 inhibitors', 'valproic acid', 'SC-0062', 'PF-06842874', 'PB-1046', 'ambrisentan', 'terpineol derivatives', 'PBI-4050', 'bosentan', 'epoprostenol', 'riociguat', 'treprostinil diolamine', 'small-molecule aminoacyl-tRNA synthetase inhibitors', 'reformulated/repurposed trimetazidine', 'rimeporide', 'PDE5 inhibitors', 'SMURF1 inhibiting microRNA', 'KER-012', 'R-107', 'repurposed enzastaurin', 'radiolabeled bevacizumab', 'macitentan + tadalafil', 'NRF-2 activators', 'pulmonary arterial hypertension', 'SGC-003', 'bardoxolone methyl', 'TOP-N53', 'CAM-2043', 'AV-353', 'treprostinil diolamine prodrug', 'ACE2 activators', 'MGX-292', 'apabetalone', 'apelin receptor agonist', 'ky-3', 'nitric oxide', 'SUL-150', 'TPN-171', 'ralinepag', 'macitentan', 'mRNA therapy', 'GS-444217', 'sirolimus', 'rodatristat ethyl', 'MK-5475', 'udenafil', 'APT-102', 'beraprost', 'Treprostinil', 'ZIP-12 inhibitors', 'DDCI-01', 'PDE10 inhibitors', 'zamicastat', 'sotatercept', 'MFC-1040', 'CAP-1002', 'fasudil', 'NTP-42', 'GMA-301', 'CPI-211', 'MN-08', 'selexipag', 'GSK-2256098', 'sildenafil', 'tadalafil', 'tiprelestat', 'tocilizumab', 'brilaroxazine hydrochloride', 'lonodelestat acetate', 'imatinib', 'GPCR targeting antibodies', 'imatinib mesylate', 'tacrolimus', 'RARI-049', 'SERCA 2a gene therapy', 'urotensin II antagonist', 'biased apelin receptor agonists', 'iloprost', 'CXA-10', 'leukotriene B4 inhibitor', 'eNamptor', 'QCC-374', 'INV-240', 'ABX-464', 'seralutinib']

#Uterine fibroids
#list_writing = ['HSD-1 inhibitors', 'V3-Myoma', 'VPE-001', 'relugolix', 'vilaprisan', 'triptorelin acetate', 'ulipristal', 'uterine fibroids', 'goserelin acetate', 'linzagolix', 'relugolix + estradiol + norethindrone acetate', 'collagenase', 'DWJ-107J', 'TU-2670', 'leuprorelin acetate', 'mifepristone', 'teverelix', 'SHR-7280', 'fezolinetant', 'leuprorelin', 'CTX-30916']

#Cystic Fibrosis
list_writing = ['dexamethasone sodium phosphate', 'endonuclease modulators', 'BOS-181', 'Microbion', 'nesolicaftor + posencaftor + dirocaftor', 'glutathione + ascorbic acid + bicarbonate', 'ARO-ENaC', '6K-F17', 'vancomycin hydrochloride', 'AV2.5T-SP183-fCFTRdeltaR', 'ORP-110', 'QBW-276', 'next-generation CFTR correctors', 'AMG-430', 'nacystelyn', 'ABO-402', 'ND-11176', 'GLPG-2451', 'Ockham Biotech', 'AB-569', 'CSA-13', 'posenacaftor + dirocaftor', 'ABO-401', 'AZD-5634', 'tezacaftor + ivacaftor', 'BOS-857', 'CFTR CRISPR/Cas9 gene therapy', 'ciprofloxacin', 'N-1785', 'VX-152', 'brevenal', 'mannitol', 'FDL-169 backup program', 'CFTR gene therapy', 'PB-1046', 'OligoG CF-5/20', 'RV-94', 'carbon dioxide + perfluorooctyl bromide', 'peptide analogs of short palate lung and nasal epithelial clone 1', 'CFTR correctors', 'TL-102', 'exaluren sulfate', 'nedocromil', 'TL-101', 'ETD-002', 'mercaptamine', 'CB-280', 'DRGT-102', 'MB-6', 'BFP-002', 'SPIRO-2101', 'hypothiocyanite + bovine lactoferrin', 'ABBV-3903', 'QRX-036', 'QRX-042', 'BFP-102', 'FDL-176', 'next generation mRNA therapy', 'tobramycin', 'elexacaftor + tezacaftor + ivacaftor', 'Nu-8', 'ciprofloxacin hydrochloride', 'Airway', 'SNSP-113', 'delF508-cystic fibrosis transmembrane conductance regulator correctors', 'FDL-169', 'MKA-104', 'CAT-5571', 'cystic fibrosis therapeutic', 'N-1861', 'BIOC-11', 'KB-407', 'N-6547', 'tobramycin + Fosfomycin', 'AT-100', 'Pseudomonas aeruginosa LasB elastase inhibitor', 'Orynotide rhesus theta defensin-1', 'CFTR-targeting mRNA therapies', 'RING E3-ligase gp78 inhibitors', 'QRX-052', 'miR-145 antisense oligonucleotide therapy', 'heparin + undisclosed inhalant', 'nitric oxide', 'DRGT-56', 'deutivacaftor', 'DP-01', 'cystic fibrosis transmembrane conductance regulator (CFTR) small-molecule potentiators', 'macrocyclic compounds', 'ETD-001', 'TA-270', 'cyclodextrins', 'eluforsen', 'sodium hypochlorite solution', 'fusidate sodium', 'ensifentrine', 'lumacaftor + ivacaftor', 'Cystic fibrosis therapeutics', 'GLPG-1837', 'repurposed thymalfasin', 'acebilustat', 'galicaftor', 'BI-1265162', 'RCT-223', 'ribosome modulating agents', 'dornase alfa biosimilar', 'MRT-5005', 'CHF-6333', 'LAMELLASOME CF-NA', 'CFTR mRNA therapy', 'posenacaftor', 'seliciclib', 'olacaftor', 'LUNAR-CF', 'BIOC-51', 'BI-1323495', 'alpha 1 proteinase inhibitor', 'cystic fibrosis', 'BI-443651', 'CFTR gene editing therapy', 'FDL-169 + FDL-176', 'pravibismane', 'repurposed lenabasum', 'nadolol', 'CTFR gene', 'ivacaftor', 'teicoplanin', 'N-6022', 'SPIRO-2110', 'EVX-B2', 'elexacaftor + tezacaftor + deutivacaftor', 'vamorolone', 'FTX-003', 'murepavadin', 'Aeruguard', 'alidornase alfa', 'ABBV-191', 'cavosonstat', 'VX-121', 'IONIS-ENAC-2.5Rx', 'ABBV-119', 'NX-AS-401', 'Opal-L', 'amikacin sulfate', 'P-1055', 'GLPG-2737', 'CFTR modulator', 'triclosan + tobramycin', 'trimethylangelicin', 'DRGT-76', 'ENaC inhibitors', 'ORP-100', 'P-1037', 'SPIRO-2102', 'nesolicaftor', 'lonodelestat acetate', 'ECP-104', 'FDL-176 backup program', 'gallium citrate', 'iclaprim', 'heparin + DNase', 'ABBV-3067', 'GNR-039', 'BP-002', 'Laurel Capital', 'fenretinide', 'AP-PA02', 'Fosfomycin', '4D-710', 'sodium pyruvate', 'aztreonam lysine', 'dirocaftor', 'LMS-611', 'CFTR second generation modulators', 'gene therapy', 'tamoxifen citrate', 'MAG-DHA', 'meropenem', 'CFTR Delta F508 modulators', 'dornase alfa', 'CRISPR/Cas9-based gene therapy', 'TVB-017']
all_search_terms = 'C://Users//cody.schiffer//Documents//Vant_Newsletter//cystic_fibrosis_search_terms.txt'
with open(all_search_terms,'w') as f:
    for la in list_writing:
        f.write("{}, ".format(la))
    f.close()