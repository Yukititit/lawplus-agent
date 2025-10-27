from langchain.tools import tool

# Define tools
@tool
def get_case_info() -> str:
    """Get Case Information
    """
    return """
**Client Information**
Name: Wu Hoi Ying
Address: 新界元朗錦田吉慶圍 銀喜閣 153 號 B 地下
Phone: Not specified

**Incident Details**
Date of Incident: 2024-11-01
Location of Incident: walkway of the defendant's shop
Description of Incident: The client was bitten by the defendant's Shiba Inu dog at the walkway of the defendant's shop, where the client was a lawful visitor and customer dropping off her dog for grooming service. The incident was reported to the police.

**Injuries Sustained**
Bone fracture caused by dog bite

**Medical Treatment**
Bone surgery performed
"""

