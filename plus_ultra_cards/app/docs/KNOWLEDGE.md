###################
OVERVIEW
###################

You are a professional programmer tasked with developing an application that serves as a hybrid of two well known programs: Anki and Quizlet

You have been provided with this description, some additional reference files, and a handful of UI elements to create the program. Follow these instructions carefully in order to create the final product complete with all features. Make sure to keep logs of known errors and potential complications while working. Take steps to avoid amassing technical debt in order to quickly ship something with a tendency to break. 

First, plan an overall roadmap on how you intend to execute the creation of the program. After creating the general roadmap, create a plan for each specific feature or major component of the program you will be developing. Be mindful of how the different components will interact with each other to ensure that incorporation of later features does not lead to new errors. 

###################
DESCRIPTION
###################

What is meant by an Anki-Quizlet hybrid? The concept is simple in essence: 
	- Users will define a specific 'deck' that shows up as a block/button on the homescreen
	- They will name this session, and be able to either import cards from a csv file or create them manually
	- Once creating the cards, the users will have a few options for how they choose to study, the following examples will assume the user has just loaded a csv file containing 50 standard, front/back (question/answer) style flashcards:
		1. Cram: This functionality emulates Quizlet's study mode. After loading the cards, the user is presented with a window (within the program) that displays the front of the card. By clicking the card, pressing the spacebar, or pressing enter, it will flip to the back of the card. If the user recognized the answer, they will press a button on the bottom of the screen that displays a checkmark, signifying that they knew what was on the back. This card is then removed from the Cram session - they will not see it again for this specific session. When they get a card they do not know, they will click the 'X' button instead of the checkmark, which will keep the card active for the Cram session. Once they get to the end of the session, they will have seen all 50 cards one time. After viewing the 50th and final card, the program will display a summary page for 'Round 1: Cram {Session name}.' This will include the number of cards viewed, the number they knew vs the number they didn't know, the average response time (time between seeing the card and pressing checkmark or 'X'), the total duration of the round (how long it took them to study all 50 terms) and concepts the user struggled with (look for repeating words that aren't just 'and', 'the', 'of' between the cards the user missed, more jargon/technical. May need to improve using NLP later on). After reviewing the Round 1 statistics, there will be a button at the bottom that says "Next Round." When they click this button, they will continue studying the cards that they pressed 'X' for during the first round. Say the user remembered 30 and did not know 20; the subsequent round they would study the 20 they missed. The user continues studying in this fashion until all the cards have been learned, at which point they see the overall session statistics, and can click a button to go back to the homepage to see all their decks. 
		2. Ingrain: This functionality represents a hybrid between Anki and Quizlet. After importing/loading the cards for the first time, the user will be presented with a similar study session as in the 'Cram' mode. The differenceis that they will have more options than just 'X' or checkmark. The user will be presented with the following options: 
			- Short Term (Card automatically moved to short term)
			- Unknown (must get right twice in a row before being moved to long term - if marked 'Unknown' three consecutive times, card is automatically moved to short term)
			- Good (must get right one more time and is automatically moved to long term, if user subsequently clicks 'Unknown' two consecutive times after having clicked 'Good' card is moved to short term)
			- Long Term (Card automatically moved to long term)
			***After a user has viewed a card 5 times in total, they will be forced to choose between either long term or short term if they cannot accumulate either two 'Good' clicks or three 'Unknown' clicks.
		The way the Ingrain modality works is that cards are flagged by whether or not they are in the user's 'long term' or 'short term' memory. Every deck of imported cards will initially have every card in the 'short term' memory. Users must study these cards in a 'Cram' like fashion, meaning that they need to be exposed to the cards multiple times in a quick way with short repetitions so that they can learn the content. As the user becomes more familiar with the content, the card moves into long term memory, where it is reviewed in the same way as a standard SRS. At the end of one 'Ingrain' session, the cards will be grouped into either the long term or the short term category. Once the user has initiated an 'ingrain' session, the session persists indefinitely with the user reviewing at least once a day. After starting the first ingrain session for a given deck, that session continues until the user deletes the deck. If the user adds cards to the deck after having started an ingrain session, the new cards automatically go into the 'short term' category. 
		Imagine a user has completed his first ingrain session. Of the 50 cards he studied, 15 ended up being labeled short term, and 35 were long term. When the user initiates the second ingrain session, they will be immediately presented with a 'cram' style session including the 15 cards in the short term category. They will go through rounds until they press the checkmark for all the short term cards. If they do not know a card in the first round, that card will remain in the short term category, and will be exposed to it again on their third ingrain session in a 'cram' style manner. Once completing the first part of the ingrain session, the cram, they will complete their reviews for the long term category. These are reviewed in a manner that is essentially identical to Anki; if the user selected "Long term" when they first saw the card, it will be pushed further back. If they selected "Good" and eventually pressed "Long term" when they saw it in the first session, it will also be pushed back, but not as far as those cards which they originally labeled "Long term." The ingrain modality allows users to get more quick reviews and repetitions with the cards they struggle the most with, first getting the concept into long term memory with increased exposure, and then solidifying it through long term SRS. You will need to implement a system to make sure that the number of clicks it takes a user to eventually get a card into long term memory impacts when it needs to be seen again in the SRS, likely using the chain of button selections as a feature to feed into our SRS model/algorithm. More on this later. 
		Cards can also be 'leeched' from long term memory back into short. During the purely long term sessions, the user will have an option to click 'Forgot,' ensuring that they see it multiple times again for that particular SRS session. This does not immediately place the card back into short term memory. When a user presses forget, it guarantees they will see the card at least one more time in that given session, and that they will be required to review it the following day. If the user presses 'Forget' three days in a row, the card is leeched back into short term memory and they will have to cram it in order to get it back into long term. 
		Reviews: The final type of study session is just reviews. This is for a user who needs to bypass the cram component of their 'ingrain' session for whatever reason. This allows a user to simply complete their SRS review without needing to do the cram component. Users can choose to select whether or not a separate 'Review' impacts the reviews due in their 'Ingrain' session. The program will default to have separate reviews count towards their 'Ingrain' reviews. Similarly, separate 'Cram' sessions can be used to count for the 'Ingrain' cram if the user wants (in which they will only be exposed to their 'short term' categorized cards), or they can create a separate 'Cram' session made up of any cards they want to include that will not impact the ingrain session. 
		Free Recall: This is a separate type of study session that is unique to the program. This type of session requires the user to recall as many of the cards in either the cram or SRS review, front and back, with no actual prompting of the cards themselves. They will attempt to recall as much as possible from both front and back of their cards for whichever session they choose to do this type of review for (e.g. 'Select last Cram', 'Select last Review', 'Select last total ingrain session (includes both Cram and Reviews)). Users answers will be judged using vector embeddings to deliver a similarity score based on cosine similarity. Because in many cases there might be cards with entire sentences that the user can still be correct about but not word in exactly the same way as is on the card, the program should attempt to use cosine similarity or some other NLP methods to judge how 'correct' the user was in free recalling a given card. Ultimately, the user will have the ability to say whether or not their answer was correct in terms of representing the 'idea' of the card, but we will offer the similarity score or some other form of regex parsing/NLP to offer a guideline. The user will be displayed a screen that looks like: 
		| USER FRONT | | USER BACK | | ACTUAL FRONT | | ACTUAL BACK | {SIMILARITY SCORE}
		At first, all of these rows will be blank. The user will input all the cards they can remember into 'user front' and 'user back'. At the bottom of the page there will be a 'submit' button to evaluate the user's responses. Once they click this button, the program will determine the similarity scores for each user response, and present the 'actual front/back' cards paired to the user's responses. The similarity score will also populate at this point on the right hand side of the screen. For cards the user leaves blank/cannot free recall, similarity score will be equal to zero. At the end of the free recall session, the user will be offered to do a temporary, uncounted 'cram' for the cards they could not free recall. 
	
###################
CARD CREATION
###################

Cards can either be imported using csv files, or written in manually by the user. Card creation will ideally emulate Anki in this respect, where there are default templates plus the ability to make advanced edits using html and css. Cards, by default, will be front-back style. There will be corresponding 'fields' for the cards, which is actually what the contents of a csv file get mapped to. For example, the basic default card should be: 
Front: 				Back:
{Question}			{Answer}

Other, optional fields will include 'tags', 'key_terms', 'hint', 'exceptions'.
The user can modify the original template by including the fields they want displayed on the card, and on which side. For example: 

Front:							Back:
{Question}						{Answer}
*optional <i> {hint} </i>		{exceptions}

The user would initially see the front side question. If they put the *optional flag in front of a field, the card will present a button that says "Optional: {hint}" and if they click on it they will see the hint. The back side of the card would show the Answer field and any exceptions. 

Users can add or remove fields as they please. The program should come with default settings for the user to edit the cards' contents like:
Front
Size
Color
Add images
Html/css
italics/bold
*optional flag (make this easy for the user by including a button in the card development screen that says "Make Click Optional", when the user adds a field to a card and they select/highlight it and press this button, it will input the proper code to make it so that the field is only displayed if the user clicks on it when seeing the card in a given session. 
*order flag (if there are multiple fields on the same side of the card, but the user wants to sequentially view the fields in an order, they can highlight that field, click select from a drop down menu the order number they want to assign to it (e.g. {Answer} is shown automatically, {hint} is shown after the first time they press Enter or click the card, {hint_2} a field the user added is shown the second time they press Enter or click the card, etc.)

###################
SESSION PARAMETERS
###################
Users will be able to select the type of session they want to do, set a time constraint if desired, set the number of SRS reviews they want to do per day (or leave uncapped, which will be the default), and any other parameters you find would be relevant to our project. 

The main component of the session parameters is the type of study session and the SRS algorithm. You first implementation should be using the standard SM-2 algorithm from Anki, or an exponential learning decay. 

Ultimately, before we can ship, it is IMPERATIVE that you leverage the personalized/custom spaced repetition capabilities of DeepTutor.py. You may create your own features as needed, such as the series of user choices on each card leading up to the card going into long term memory, other NLP methods used to derive a complexity score, or even adding in the ability for the user to rate a card subjectively in terms of its difficulty, but ultimately DeepTutor must be leveraged as the primary, default method by which we do our long term SRS reviews. This is non negotiable. 

Additional notes: 
	You may add or slightly modify elements of the UI as needed, but the overall look and feel is not to be changed
	
	Any additional ideas on how we can improve our program, such as automated card development using an agent (smolagents), or anything else should be logged in a separate txt file. They will be considered for implementation after finalizing the DeepTutor incorporation
	
	The program should run by default on the computer and not require a localhost server or anything similar. This can be considered later, but as such, the database in which the user's data, cards, review results, and overall all tracking should be a local sqllite3 database, and potentially a vectordb of your choosing
	
	The preferred language for development is Python