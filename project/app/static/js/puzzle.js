// Puzzle.js

// JQuery objects; stored to prevent multiple calls
const word_div = $(".puzzle__words");
const letter_div = $(".puzzle__letters");
const turns_div = $(".puzzle__counter");
const toast_div = $(".toast-body");

// Called by keyboard inputs
const submit_word = $("#submit-word");
const shift_right = $("#shift-right");

// URLS and user id
let url_load = "";
let url_check = "";
let url_stats = "";
let user_id = "";

// Puzzle class; each instance represents a new daily puzzle
class Puzzle {
	constructor() {
		this.words = []; // Array of word objects
		this.letters = []; // Array of all non-unique letter objects
		this.slots = []; // Array of unique slot objects
		this.unique = {}; // Letter value : unique letter object
		this.active = 0; // Index of active word in words array
		this.rotation = 0; // Rotation of the puzzle triangle
		this.keyboard = false; // Whether keyboard inputs should trigger events other than shift
		this.transform = true; // Whether shifting words should trigger rotation effect
	}

	// Initialises puzzle
	initPuzzle() {
		// Get puzzle data from server
		let response = $.ajax({
			method: "PUT",
			url: url_load,
			async: false,
			contentType: "application/json"
		});
		// Server request succeeded
		response.done((data) => {
			// Parse data
			let letters = JSON.parse(data.letters);
			let unique = JSON.parse(data.uniqueletters);
			let lpos = JSON.parse(data.lpositions);
			let gpos = JSON.parse(data.gpositions);
			// Loop through letters
			for (let i = 0; i < 12; i++) {
				// Create letter
				let str = letters[i].toUpperCase();
				if (!this.unique.hasOwnProperty(str)) { this.unique[str] = new UniqueLetter(unique[i], str) };
				this.letters.push(this.unique[str].createLetter());
				// Create slot
				let slot = new Slot(i);
				slot.states = gpos[i];
				this.slots.push(slot);
			}
			// Create words
			for (let i = 0; i < 3; i++) {
				let slots = this.slots.slice(4 * i, 4 * i + 5);
				if (i == 2) { slots.push(this.slots[0]) };
				let div = $("#word-" + (i + 1));
				this.words.push(new Word(i, div, slots));
				slots.forEach((slot) => { slot.createElement(div) });
			}
			// Load letter positions
			for (let i = 0; i < 12; i++) {
				if (lpos[i]) {
					let index = letters.indexOf(lpos[i].toLowerCase());
					letters[index] = 0;
					this.slots[i].setLetter(this.letters[index]);
				}
			}
			// Set starting values
			this.resetActiveWord();
			this.setTurns(10 - data.guessCount);
			if (data.status) { this.endGame(data.status - 1) }
			else { this.enableButtons(true); this.keyboard = true; this.loadStats("user"); };
		});
		// Server request failed
		response.fail(() => { $(".puzzle__display").text("Puzzle could not be loaded. Please refresh the page to try again.") });
		// Fade out loading overlay
		response.always(() => { $(".body__overlay").fadeOut("slow") });
	}

	// Removes all DOM elements and event listeners associated with puzzle
	emptyPuzzle() {
		// Empty appended elements
		letter_div.empty();
		toast_div.empty();
		turns_div.empty();
		$(".graph, .statistic").empty();
		$(".puzzle__words > .word").empty();
		// Reset puzzle values
		this.resetActiveWord();
		this.setTurns(0);
		this.words = [];
		this.letters = [];
		this.slots = [];
		this.unique = {};
		// Disable all buttons
		this.enableButtons(false);
		this.keyboard = false;
	}

	// Reconstruct puzzle with new user/data
	reconstructPuzzle() {
		let overlay = $(".puzzle__overlay");
		overlay.fadeIn();
		this.emptyPuzzle();
		this.initPuzzle();
		overlay.delay(200).fadeOut("slow");
	}

	// Returns active or all words as an array
	getWordArray(all) {
		let arr = ["None", "None", "None"];
		if (all) {
			for (let i = 0; i < this.words.length; i++) { arr[i] = this.words[i].getString() };
		} else {
			arr[this.active] = this.getActiveWord().getString();
		}
		return arr;
	}

	// Gets active word
	getActiveWord() {
		return this.words[this.active];
	}

	// Sets turns remaining
	setTurns(num) {
		this.turns = num;
		turns_div.text("Turns remaining: " + this.turns);
	}

	// Shifts active word right if direction is true, or left if false
	shiftActiveWord(direction) {
		this.getActiveWord().setActive(false);
		if (direction) {
			this.active == 2 ? this.active = 0 : this.active++;
			this.rotation += 120;
		} else {
			this.active == 0 ? this.active = 2 : this.active--;
			this.rotation -= 120;
		}
		if (this.transform) { word_div.css("transform", "rotate(" + this.rotation + "deg)") };
		this.getActiveWord().setActive(true);
	}

	// Resets active word to first index
	resetActiveWord() {
		if (this.active != 0) {
			this.words[this.active].setActive(false);
			this.active = 0;
		}
		this.rotation = 0;
		word_div.css("transform", "rotate(0deg)");
		this.words[0].setActive(true);
    }

	// Returns letters to letter div
	resetSlotLetters() {
		this.slots.forEach((slot) => { slot.setLetter(null) });
	}

	// Verifies one or all words
	verifyWord(all) {
		// Disable temporarily
		this.keyboard = false;
		$(".puzzle__buttons > button").prop("disabled", true);
		// Get word array
		let word = this.getWordArray(all);
		// Sends a guess to server for verification
		let response = $.ajax({
			method: "POST",
			url: url_check,
			async: false,
			data: JSON.stringify(word),
			dataType: "json",
			contentType: "application/json"
		});
		// Server request succeeded
		response.done((data) => {
			if (data.success) {
				let result = JSON.parse(data.response);
				this.setTurns(this.turns - 1);
				for (let i = 0; i < 3; i++) {
					if (result[i] == "None") { continue }; // Only check submitted words
					this.words[i].setSlotStates(result[i]); // Display letter states
				}
				// Checks if game should end
				if (data.status) {
					this.endGame(data.status - 1);
					$("#view-results").trigger("click");
				};
			} else { this.displayAlert(data.message) };
		});
		// Server request failed
		response.fail(() => { this.displayAlert("Looks like something went wrong...") });
		response.always(() => { this.keyboard = true; $(".puzzle__buttons > button").prop("disabled", false); });
    }

	// Ends game and displays result; true if won else false
	endGame(result) {
		// Disable puzzle buttons and events
		this.enableButtons(false);
		this.keyboard = false;
		// Replace puzzle buttons with view results button
		$("#view-results").show();
		$(".puzzle__buttons > button").not("#view-results").hide();
		// Load game stats
		this.loadStats("user");
		this.loadStats("population");
		let str = "Have you tried today's Word Trinity? Can you beat the average guesses?";
		// Display results
		if (result) {
			turns_div.text("Game won");
			$(".results__title").text("You won!");
			str += " I beat it in " + (10 - this.turns) + " turns!";
		} else {
			turns_div.text("Game over");
			$(".results__title").text("You lost!");
			$(".word__slot").addClass("disabled");
			str += " I couldn't beat it!"
		}
		// Chnage share buttons
		let link = window.location.href;
		let obj = { title: "WordTrinity", text: str, url: link };
		$(".twitter-share-button").attr("data-text", str);
		if (!navigator.share) { $("#share-results").hide() } else { $("#share-results").show().click(() => { navigator.share(obj) }) };
	}

	// Adds an alert to DOM
	displayAlert(msg) {
		let toast = new bootstrap.Toast(document.getElementById("puzzle-toast"))
		toast_div.text(msg);
		toast.show();
	}

	// Requests and displays server statistics
	loadStats(param) {
		let target;
		param == "user" ? target = $("#stats") : target = $(".results__stats");
		let request = $.get(url_stats, { userid: user_id, type: param }, (data) => {
			if (data.success) {
				let graph = target.find(".graph").empty();
				let guesses = JSON.parse(data.userGuesses);
				let sum = data.totalGuesses;
				for (let i = 0; i < 10; i++) {
					let percent = ((guesses[i] / sum) * 100).toString() + "%";
					let row = $("<div class='row'><div class='col-1'>" + (i + 1) + "</div></div>").appendTo(graph);
					let col = $("<div class='col'></div>").appendTo(row);
					$("<div class='bar'>" + guesses[i] + "</div>").appendTo(col).css("width", percent);
				}
				if (param == "user") { // User statistics
					$(".user-winrate").text(data.userwinrate);
					$(".population-winrate").text(data.winrate);
					$(".population-guesses").text(data.averageGuesses);
				} else { // Puzzle statistics
					$(".user-guesses").text(10 - this.turns);
					$(".puzzle-winrate").text(data.winrate);
					$(".puzzle-guesses").text(data.averageGuesses);
                }
			} else { target.text(data.message) }
		});
		request.fail(() => { target.text("Game statistics could not be loaded. Please refresh the page and try again.") });
    }

	// Disable rotation transforms if the window width is < 200 px
	resizePuzzle() {
		$(window).width() < 200 ? this.transform = false : this.transform = true;
		this.resetActiveWord();
	}

	// Binds or unbinds event listeners depending on game state
	enableButtons(bool) {
		if (bool) {
			$(".puzzle__letters > button").click((event) => { this.onLetterClicked(event) });
			$(".word__slot").click((event) => { this.onSlotClicked(event) });
			$("#reset-letters").click(() => { this.resetSlotLetters() });
			submit_word.click(() => { this.verifyWord(false) });
			$("#submit-puzzle").click(() => { this.verifyWord(true) });
		} else {
			$(".puzzle__letters > button").off().prop("disabled", true);
			$(".word__slot").off();
			$("#reset-letters").off().prop("disabled", true);
			submit_word.off().prop("disabled", true);
			$("#submit-puzzle").off().prop("disabled", true);
        }
	}

	// Adds letter to active slot
	onLetterClicked(event) {
		let index = $(event.target).index();
		let letter = this.letters[index];
		if (!letter.disabled) {
			let word = this.getActiveWord();
			let slot = word.getFocusedSlot();
			slot.setLetter(letter);
			word.shiftFocusedSlot(true);
		}
	}

	// Changes slot to clicked slot
	onSlotClicked(event) {
		let target = $(event.target);
		let index = target.index();
		let word = target.parent().index();
		if (this.active == word) { this.getActiveWord().setFocusedSlot(index) };
	}

	// Triggers events based on key press
	onKeyUp(event) {
		// Check for modifier keys
		if (event.shiftKey || event.altKey || event.ctrlKey || event.metaKey) { return };
		// Check for open modals
		if ($(".modal.show").length) { return };
		// Get keycode
		let code = event.keyCode;
		if (code == 32) { shift_right.trigger("click"); return; };
		// Only triggered if keyboard input is allowed
		if (this.keyboard) {
			if (code <= 90 && code >= 65) { // Check if key is a letter
				let key = (event.key).toUpperCase();
				if (this.unique.hasOwnProperty(key)) { // Check if letter is allowed
					let letter = this.unique[key].getLetter();
					if (letter) {
						if (letter.slot > -1) { this.slots[letter.slot].setLetter(null) };
						let word = this.getActiveWord();
						word.getFocusedSlot().setLetter(letter);
						word.shiftFocusedSlot(true);
					} else { this.displayAlert("The letter " + key + " cannot be used anymore!") }
				} else { this.displayAlert("The letter " + key + " is not allowed!") };
			} else {
				switch (code) {
					case 8: // Backspace
						let word = this.getActiveWord();
						let slot = word.getFocusedSlot();
						if (slot.letter) { slot.setLetter(null) } else { word.shiftFocusedSlot(false) };
						break;
					case 13: // Enter
						submit_word.trigger("click");
						break;
					case 37: // Left arrow
						this.getActiveWord().shiftFocusedSlot(false);
						break;
					case 39: // Right arrow
						this.getActiveWord().shiftFocusedSlot(true);
						break;
				}
			}
        }
    }
}

// Word class; each instance holds a reference to one or more Slot objects
class Word {
	constructor(index, element, slots) {
		this.index = index; // Index of word
		this.element = element; // Reference to DOM element
		this.slots = slots // Array of slot objects associated with word
		this.active = false;  // Whether word is currently active
		this.focus = 0; // Index of focused slot in local slots array
	}

	// Get word as a string
	getString() {
		let str = "";
		for (let i = 0; i < this.slots.length; i++) { str += this.slots[i].getLetterValue() };
		return str;
	}

	// Returns index of next slot that is not disabled; direction is right if true, left if false
	getNextSlot(index, direction) {
		for (let i = 0; i < this.slots.length; i++) {
			if (direction) { index < 4 ? index++ : index = 0 } else { index > 0 ? index-- : index = 4 };
			if (!this.slots[index].disabled) { return index };
		}
		return -1;
	}

	// Returns focused slot
	getFocusedSlot() {
		return this.slots[this.focus];
	}

	// Sets a different slot as focused slot
	setFocusedSlot(index) {
		this.focus = index;
		let selector = ":nth-child(" + (index + 1) + ")";
		this.element.children().removeClass("start");
		this.element.children(selector).addClass("start");
	}

	// Sets next slot that isn't disabled as focused; direction is right if true, left if false
	shiftFocusedSlot(direction) {
		let next = this.getNextSlot(this.focus, direction);
		if (next >= 0) { this.setFocusedSlot(next) };
	}

	// Sets focused slot to beginning
	resetFocusedSlot() {
		if (this.slots[0].disabled) {
			let start = this.getNextSlot(0, true);
			if (start > -1) { this.setFocusedSlot(start) };
		} else { this.setFocusedSlot(0) };
    }

	// Sets word as active
	setActive(bool) {
		this.active = bool;
		if (bool) {
			this.resetFocusedSlot();
			this.element.addClass("active");
		} else {
			this.element.removeClass("active");
		}
	}

	// Sets states of slots based on array of numbers
	setSlotStates(arr) {
		for (let i = 0; i < this.slots.length; i++) { this.slots[i].setState(arr[i]) };
		if (this.getFocusedSlot().disabled == true) { this.shiftFocusedSlot(true) };
	}

}

// Slot class; each instance holds a reference to one or more slot DOM elements
class Slot {
	constructor(index) {
		this.index = index; // Integer represent index of unique slot
		this.elements = []; // Holds an array of DOM references
		this.states = []; // Array holding all possible letter states
		this.letter = null; // Non-unique letter associated with slot
		this.disabled = false; // Whether the slot letter can be changed
	}

	// Creates and returns a slot element in DOM
	createElement(parent) {
		let slot = $("<div class='word__slot slot'></div>").appendTo(parent);
		this.elements.push(slot);
		return slot;
	}

	// Returns a string representing the letter value
	getLetterValue() {
		if (this.letter) { return (this.letter.value).toLowerCase() } else { return "" };
	}

	// Replace existing letter with new letter
	setLetter(letter) {
		if (!this.disabled) {
			// Remove old letter
			if (this.letter) { this.letter.setSlot(-1) };
			// Add new letter
			if (letter) {
				this.letter = letter;
				this.elements.forEach((el) => { el.text(letter.value); });
				this.displayState(this.states[letter.index]);
				letter.setSlot(this.index);
			} else {
				this.letter = null;
				this.displayState(0);
				this.elements.forEach((el) => { el.text("") });
            }
        }
	}

	// Sets slot as disabled and unbinds event listener
	setDisabled(bool) {
		this.disabled = bool;
		this.letter.setDisabled(bool);
		if (bool) { this.elements.forEach((el) => { el.off() }) };
    }

	// Update a letter's state in state array
	setState(num) {
		if (this.letter) {
			let unique = this.letter.index;
			this.states[unique] = num;
			this.displayState(num);
        }
	}

	// Displays state change
	displayState(num) {
		this.elements.forEach((el) => {
			el.removeClass("state-1 state-2 state-3 state-4");
			if (num) { el.addClass("state-" + num) };
			if (num == 4) { this.setDisabled(true) };
        })
	}

}

// Unique letter class; each instance holds a reference to one or more Letter objects
class UniqueLetter {
	constructor(index, value) {
		this.index = index; // Integer representing index of unique letter
		this.letters = []; // Array holding all letters with this value
		this.value = value; // Value of letter as string
	}

	// Creates and returns letter object
	createLetter() {
		let div = $("<button class='slot'>" + this.value + "</button>").appendTo(letter_div);
		let letter = new Letter(div, this.index, this.value);
		this.letters.push(letter);
		return letter;
    }

	// Get best letter to use; unused > used > null
	getLetter() {
		let arr = this.letters.filter((letter) => { return !letter.disabled });
		if (arr.length > 0) {
			for (let i = 0; i < arr.length; i++) { if (arr[i].slot <= -1) { return arr[i] } };
			return arr[0];
		}
		return null;
    }
}

// Letter class; each instance holds a reference to one letter DOM element
class Letter {
	constructor(element, index, value) {
		this.element = element; // Reference to DOM element
		this.index = index; // Index of unique letter
		this.value = value; // Value of letter as string
		this.disabled = false; // Whether this letter can be used
		this.slot = -1; // Index of current slot; -1 if none
	}

	// Sets index of slot containing letter
	setSlot(index) {
		this.slot = index;
		index > -1 ? this.element.prop("disabled", true) : this.element.prop("disabled", false); // greys out appearance only
	}

	// Sets slot to disabled
	setDisabled(bool) {
		this.disabled = bool;
		this.element.prop("disabled", bool);
    }
}