"""
Generate documentary narration audio using edge-tts.
Each segment corresponds to a chapter/section of the documentary.
"""
import asyncio
import edge_tts
import os

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
VOICE = "en-US-GuyNeural"
RATE = "-8%"
PITCH = "-3Hz"

segments = {
    "00_intro": (
        "For Sale. "
        "From the Big Bang to the blockchain, energy has always flowed toward "
        "whoever can concentrate it. The only thing that changes is the tool, "
        "and the speed."
    ),

    "01_beginning": (
        "In the beginning, there was nothing. Then there was everything. "
        "Thirteen point eight billion years ago, all matter and energy in the universe "
        "existed in a point smaller than an atom. It exploded. Hydrogen formed. "
        "Gravity pulled it together. Stars ignited. Stars died. Their deaths created "
        "heavier elements. Carbon. Oxygen. Iron. Those elements formed planets. "
        "On one planet, chemistry became biology. "
        "For four billion years, life was simple. Single cells. Then multicellular organisms. "
        "Then something remarkable: competition. The moment two organisms wanted the same "
        "resource, the game began. "
        "The rules were set by physics. Energy flows toward whoever can capture and "
        "concentrate it most efficiently. Stars do it with gravity. Cells do it with membranes. "
        "Empires do it with armies. Corporations do it with lobbyists. "
        "The mechanism changes. The law never does."
    ),

    "02_dinosaurs": (
        "Two hundred and fifty two million years ago, ninety six percent of all species "
        "were wiped out in the Great Dying. What filled the vacuum? Dinosaurs. "
        "The most successful large animals in Earth's history. They dominated for "
        "one hundred and sixty five million years. Unchallenged. Unchallengeable. "
        "Then a seven and a half mile rock hit the Yucatan at forty five thousand "
        "miles per hour. One hundred and sixty five million years of dominance, "
        "ended in a single day. "
        "The lesson: no amount of power protects you from a force you didn't see coming. "
        "Small mammals survived in the margins. They inherited everything."
    ),

    "03_humans_to_2008": (
        "Three hundred thousand years ago, Homo Sapiens arrived. Not the strongest, "
        "not the fastest. But the species that could tell stories. "
        "Language let humans coordinate at scale. Myths, religions, laws, currencies. "
        "All stories that let strangers cooperate. "
        "Three thousand years before Christ, the pyramids rose. The first megastructures. "
        "Built by centralized power extracting labor and resources. "
        "The original too big to fail. "
        "Sixteen thirty seven. Tulip mania. A single bulb traded for more than a house. "
        "Seventeen twenty. The South Sea Bubble. Parliament bribed with stock. "
        "Isaac Newton lost twenty thousand pounds. "
        "Nineteen twenty. Charles Ponzi. Fifty percent returns in forty five days. "
        "Every crypto fraud since follows the same blueprint. "
        "Nineteen forty five. ENIAC. Thirty tons. Eighteen thousand vacuum tubes. The first computer. "
        "Nineteen fifty eight. Jack Kilby and Robert Noyce invent the microchip. "
        "A single silicon chip replaces thousands of components. Moore's Law begins. "
        "Transistor density doubles every two years. The exponential curve that will reshape civilization. "
        "Nineteen fifty six. John McCarthy coins artificial intelligence. Researchers predict "
        "human level AI within twenty years. Funding pours in. Then it doesn't deliver. "
        "Two AI winters follow. Billions wasted on promises. The pattern: "
        "hype, funding, disappointment, collapse. Hype, funding, disappointment, collapse. "
        "Two thousand and one. Enron. Seventy four billion in shareholder value, destroyed. "
        "The man who cleaned up the mess? John Ray the Third. Remember that name. "
        "Two thousand and eight. The financial crisis. Ten trillion dollars in household "
        "wealth, evaporated. The banks got seven hundred billion in bailouts. "
        "Zero executives went to prison. "
        "One person published a whitepaper in response."
    ),

    "03b_ai_pattern": (
        "Every generation promises artificial intelligence will change everything. "
        "Every generation is right. Just not in the way they promised. "
        "Nineteen fifty. Alan Turing asks: can machines think? "
        "Nineteen fifty six. The Dartmouth Conference predicts AI in twenty years. "
        "Nineteen seventy four. The first AI winter. Funding collapses. "
        "Nineteen eighty. Expert systems boom. Japan spends eight hundred and fifty million. "
        "Nineteen eighty seven. The second AI winter. Every promise broken. "
        "Nineteen ninety seven. Deep Blue beats Kasparov. IBM's stock rises eighteen billion dollars. "
        "Twenty twelve. Deep learning. Video game chips crack image recognition. "
        "Google, Facebook, Amazon realize they can predict human behavior. "
        "Twenty twenty two. Chat G P T. One hundred million users in two months. "
        "The fastest growing consumer application in history. "
        "Open A I, a nonprofit founded to ensure AI benefits all humanity, "
        "pivots to a for-profit structure. Its founder lobbies Congress for regulation "
        "that only the biggest companies can afford. "
        "NVIDIA becomes the most valuable company on Earth. Three trillion dollars. "
        "Five hundred firms lobby Congress on AI. "
        "The Stargate project. Five hundred billion dollars for AI data centers. "
        "Announced from the White House. "
        "The tool built to simulate intelligence becomes the latest tool "
        "for concentrating power."
    ),

    "04_crypto_promise": (
        "On October thirty first, two thousand and eight, six weeks after Lehman Brothers "
        "collapsed, a pseudonymous figure called Satoshi Nakamoto published the Bitcoin "
        "whitepaper. Money without banks. Transactions without trust. A financial system "
        "that couldn't be corrupted because no one controlled it. "
        "For a while, the dream held. Then the money showed up. "
        "By twenty seventeen, Bitcoin hit twenty thousand dollars. By twenty twenty one, "
        "sixty nine thousand. Total crypto market cap peaked at three trillion dollars. "
        "And with the money came exactly the same people the technology was supposed to "
        "make obsolete. The fraudsters. The lobbyists. The politicians for hire. "
        "The tool built to fight corruption became the most efficient corruption machine "
        "ever created."
    ),

    "05_ftx_machine": (
        "Sam Bankman-Fried built F T X into a thirty two billion dollar empire in three years. "
        "One hundred and thirty four shell entities across twenty seven jurisdictions. "
        "A single line of code exempted his hedge fund, Alameda Research, from auto-liquidation. "
        "Every other user got liquidated at zero. Alameda could carry a negative balance "
        "up to sixty five billion dollars. "
        "Eight billion dollars in customer funds were stolen and spent on celebrity endorsements, "
        "Bahamas real estate, private jets, and political donations."
    ),

    "06_six_days": (
        "November second, twenty twenty two. CoinDesk reveals Alameda's balance sheet. "
        "Its biggest asset? A token that F T X created itself. "
        "November sixth. Binance's C Z dumps five hundred and twenty nine million in that token. "
        "One billion withdrawn in one day. "
        "November seventh. Bankman-Fried tweets: F T X is fine. Assets are fine. "
        "Behind the scenes: four billion more in withdrawals. "
        "November eighth. F T X removes the withdrawal button entirely. "
        "November eleventh. Bankruptcy. One hundred and thirty four entities file Chapter Eleven. "
        "John Ray the Third, the man who cleaned up Enron, takes over. "
        "He says: Never in my career have I seen such a complete failure of corporate controls. "
        "That night, hackers drain four hundred and seventy seven million from F T X wallets."
    ),

    "07_revolving_door": (
        "F T X didn't just lobby the regulators. It hired them. "
        "Thirteen former C F T C officials were on F T X's payroll. "
        "The acting chair. Two commissioners. The general counsel. Risk analysts. Economists. "
        "One in three members of Congress took F T X money. "
        "Forty million to Democrats, publicly. Twenty four and a half million to Republicans, "
        "in the dark. When asked to return stolen customer funds, seventy three percent "
        "of Congressional recipients didn't even respond. "
        "In the Bahamas, Bankman-Fried offered to pay off the country's entire "
        "eleven point six billion dollar national debt."
    ),

    "08_takeover": (
        "Bankman-Fried went to prison. The industry took notes, and did it better. "
        "Two hundred and forty five million dollars bought the twenty twenty four election. "
        "Fairshake, the crypto super PAC, raised two hundred and sixty million dollars. "
        "It unseated the chair of the Senate Banking Committee with forty million in attack ads. "
        "It took out Jamaal Bowman for twelve million. Katie Porter for ten million. "
        "Win rate: thirty three out of thirty five races. "
        "The mere threat of that money became a weapon. Eighteen Democrats switched their votes "
        "on the GENIUS Act stablecoin bill under threat of PAC spending against them."
    ),

    "09_pardons": (
        "Three crypto pardons in ten months. "
        "January twenty first, twenty twenty five. Day one of the presidency. "
        "Ross Ulbricht, creator of Silk Road. Life without parole, commuted. "
        "The price: Libertarian Party support in the election. "
        "March twenty seventh. The BitMEX founders. The first time a president pardoned "
        "a corporation. "
        "October twenty third. Changpeng Zhao, founder of Binance. Convicted of enabling "
        "money laundering. Pardoned after Binance paid a lobbyist, a friend of Trump Junior, "
        "four hundred and fifty thousand dollars a month for, quote, executive relief "
        "from the White House. A former Department of Justice pardon attorney called it "
        "corruption. The president told Sixty Minutes: I don't know him."
    ),

    "09b_facebook": (
        "In two thousand four, a Harvard sophomore launched a website to rate his classmates' faces. "
        "Within two years, it was open to the world. Move fast and break things. "
        "By twenty twelve, Facebook had one billion users. I P O at one hundred and four billion dollars. "
        "The product was attention. The customer was the advertiser. The user was the supply. "
        "Twenty sixteen. Russian operatives ran disinformation reaching one hundred and twenty six million Americans. "
        "Cambridge Analytica harvested eighty seven million users' data without consent. "
        "Zuckerberg called it pretty crazy to think Facebook influenced the election. "
        "Twenty eighteen. He testified before Congress for ten hours. "
        "When a senator asked how Facebook makes money, he smirked. Senator, we run ads. "
        "Twenty nineteen. Five billion dollar FTC fine. The largest privacy fine in history. "
        "Facebook's stock went up. Wall Street had expected worse. One month of revenue. Cost of doing business. "
        "Twenty twenty one. Whistleblower Frances Haugen leaked thousands of internal documents. "
        "Facebook knew Instagram was toxic for teen girls. Knew its algorithm amplified hate speech. "
        "Knew it was used to organize ethnic violence in Myanmar and Ethiopia. "
        "Internal researchers flagged the problems. Management chose growth. "
        "Then Zuckerberg renamed the company Meta and bet forty six billion on the metaverse. "
        "A rebrand to escape the brand. The metaverse is empty. "
        "January twenty twenty five. Zuckerberg writes a one million dollar inauguration check. "
        "Eliminates fact checking. Calls Trump's election a cultural tipping point. "
        "The FTC antitrust case is dismissed the same year. "
        "The man who was once hauled before Congress now pays tribute to it."
    ),

    "10_big_tech": (
        "Every major tech CEO wrote a one million dollar check to the inauguration. "
        "Zuckerberg. Bezos. Cook. Pichai. Altman. "
        "Elon Musk skipped the inauguration check and spent two hundred and eighty eight "
        "million on the election itself. The largest individual political donation "
        "in American history. "
        "In return, he runs DOGE with access to every federal agency. "
        "His companies hold thirty eight billion dollars in government contracts. "
        "He has cut staff and budgets at all seven agencies where his companies hold contracts. "
        "None of his own companies' contracts have been touched. "
        "The White House says Musk decides for himself when he has a conflict of interest."
    ),

    "11_president_profits": (
        "The president holds up to eleven point six billion dollars in cryptocurrency. "
        "He launched a memecoin three days before inauguration that peaked at seventy four "
        "dollars. He signed an executive order creating a Strategic Bitcoin Reserve. "
        "Not a single economist surveyed agreed it benefits the economy. "
        "But it makes his portfolio go up. "
        "His family receives seventy five percent of proceeds from World Liberty Financial "
        "token sales. A UAE national security adviser bought forty nine percent of the venture "
        "for half a billion dollars, days before inauguration. "
        "The man who called Bitcoin a scam in twenty twenty one now profits from every "
        "executive order he signs about it."
    ),

    "12_closing": (
        "The universe took thirteen point eight billion years to create life. "
        "Dinosaurs dominated for one hundred and sixty five million years. "
        "The pyramids took generations. "
        "Rome lasted a thousand years. Its senators were bought with gold. "
        "The Crusades were funded by banks. The banks took the trade routes. "
        "World War One killed twenty million. Arms makers sold weapons to both sides. "
        "World War Two killed seventy five million. Corporations traded with the enemy. "
        "Not one was prosecuted. "
        "The microchip took a decade to change everything. "
        "AI was promised in twenty years. It took sixty seven. "
        "Facebook connected three billion people. Then sold them. "
        "The War on Terror cost eight trillion dollars. The Taliban won anyway. "
        "Enron took a decade. Wall Street took decades. "
        "F T X took three years. Collapsed in six days. "
        "The crypto takeover of the United States government took ten months. "
        "The only thing that changes is the speed. "
        "The game never changes."
    ),
}


async def generate_all():
    for name, text in segments.items():
        output_file = os.path.join(OUTPUT_DIR, f"{name}.mp3")
        print(f"Generating {name}... ({len(text)} chars)")
        communicate = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH)
        await communicate.save(output_file)
        print(f"  -> {output_file}")
    print("\nDone! All segments generated.")


if __name__ == "__main__":
    asyncio.run(generate_all())
