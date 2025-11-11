from langchain.tools import tool


# Define tools
@tool
def read_docucment() -> list[dict]:
    """Read specific document in the case."""

    return """
香港中文大學醫院 CUHK Medical Centre Pioneering Solutions in Healthcare 開拓醫護新領域 OFFICIAL RECEIPT 正式收據 Original 正本 Patient Name 病人姓名 : WU, Hoi Ying 胡愷瑩 Receipt No 收據號碼 : OR-24110100933 Patient No. 病人號碼 : WHY1040 Receipt Date 收據日期 : 01 NOV 2024 Invoice No. 賬單號碼 : INV-24110100914 Print Date 列印日期 : 01 NOV 2024 / 16:41:31 Payment Date Payment Method Reference Number Amount 金額 付款日期 付款方法 參考號碼 (HK$ 港幣 ) 01 NOV 2024 Master Card 830009444837071557 520.00 TOTAL PAYMENT 總付款金額 520.00 Note 摘錄 1. This receipt is only valid when hospital chop is imprinted. 1. 此收據需待蓋上醫院印章後作買。 2. Please review and retain this original and notify us for any adjustment. 2. 此收據如有任何錯漏 , 敬請通知本院並保留此正本以便辦理更正手續。 3. The refund will be returned according to original payment. 3. 如需退款將會根據付款方法直接退還。 CUHK MEDICAL CENTRE RECEIVED PAYMENT WITH THANKS 香港中文大學醫院 (V02-20230610) 頁 Page 1/1
"""
