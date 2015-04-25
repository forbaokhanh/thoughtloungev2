"use strict";

var globals = {};

$(document).ready(refreshUser);

function refreshUser() {
    getCurrentUser().then(function(user) {
        globals.currentUser = user;
        console.log(globals.currentUser.id);
        if (globals.currentUser) {
            $.ajax({
                type: 'GET',
                url: "/api/users/" + user.id + "/lounges/", // MY CONSOLE SAYS THERE'S A PROBLEM HERE
                async: false,
                data: $.param({time: 'past'})
            }).then(function(userLounges) {
                globals.currentUser.userLounges = userLounges;
                globals.currentUser.loungePlurality = (userLounges.items.length == 1) ? 'lounge' : 'lounges';
            });
        }
    });
    if (typeof hostHref !== "undefined") {
        getResource(hostHref).then(function(host) {
            globals.hostToPreview = host;
        });
    }
}

$('#signInForm').submit(function(event) {
    event.preventDefault();
	
    function userSignInAuthError() {
		$('#sign-in-error').html(error('You supplied an incorrect password. Try again.'));
		return;
	}

	function userSignInNotFoundError() {
		$('#sign-in-error').html(error('We don\'t have an account with this email. You can create one at the top right.'));
		return;
	}

	function userSignInError() {
		$('#sign-in-error').html(error('We couldn\'t sign you in. Please refresh the page to try again.'));
		return;
	}

    $.ajax({
        type: 'POST',
        url: '/api/auth/sign_in/',
        data: $('#signInForm').serializeJSON(),
        contentType: 'application/json'
    }).done(function(user, textStatus, jqXHR) {
        window.location.replace('/user/')
    }).fail(function(error, textStatus, jqXHR) {
        if (error.status == 403) {
            userSignInAuthError();
        }
        else if (error.status == 404) {
            userSignInNotFoundError();
        } 
        else {
            userSignInError();
        }
    });
});

$('#signOutForm').submit(function(event) {
    event.preventDefault();
	
    function userSignOutError() {
		$('#sign-in-error').html(error('We couldn\'t sign you out. Please refresh the page to try again.'));
		return;
	}

    $.ajax({
        type: 'POST',
        url: '/api/auth/sign_out/',
        contentType: 'application/json'
    }).done(function(data, textStatus, jqXHR) {
        window.location.replace('/')
    }).fail(function(error, textStatus, jqXHR) {
        userSignOutError();
    });
});

$('#signUpForm').submit(function(event) {
    event.preventDefault();

	function userRegisterConflictError() {
		$('#signUpError').html(error('This email is already registered. Please choose a different email.'));
		return;
	}

	function userRegisterError() {
		$('#signUpError').html(error('We couldn\'t make your account. Please refresh the page to try again.'));
		return;
	}

    var data = $('#signUpForm').serializeObject();
    data.notifications = 2;
	$.ajax({
		type: 'POST',
		url: '/api/users/',
		data: JSON.stringify(data),
		contentType: 'application/json'
	}).done(function(user, textStatus, jqXHR) {
        window.location.replace('/user/');
	}).fail(function(error, textStatus, jqXHR){
		if (error.status == 409){
			userRegisterConflictError();
		}
		else {
			userRegisterError();
		}
	})
})
