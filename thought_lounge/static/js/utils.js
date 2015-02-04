"use strict";

// Source: http://stackoverflow.com/a/1186309/3024025
$.fn.serializeObject = function() {
    var o = {}
    var a = this.serializeArray();
    $.each(a, function() {
        if (o[this.name] !== undefined) {
            if (!o[this.name].push) {
                o[this.name] = [o[this.name]];
            }
            o[this.name].push(this.value || '');
        } else {
            o[this.name] = this.value || '';
        }
    });
    return o;
};

$.fn.serializeJSON = function() {
    return JSON.stringify(this.serializeObject());
};

function getArguments(args) {
    return Array.prototype.slice.call(args);
}

function formatDateTime(dateTime) {
    return moment(dateTime).format('dddd, D MMMM [at] h:mm a');
}

function formatDate(dateTime) {
    return moment(dateTime).format('dddd, D MMMM YYYY');
}

function formatISODate(dateTime) {
    return moment(dateTime).format('YYYY-MM-DD');
}

function formatISOTime(dateTime) {
    return moment(dateTime).format('HH:mm');
}

function notification(type, message) {
    if (type == 'error') {
        var alertClass = 'alert-danger';
        var alertPrefix = 'An error occurred.';
    } else {
        var alertClass = 'alert-success';
        var alertPrefix = 'Success!';
    }

    var template = '<div class="col-sm-12"><div class="alert {{ alertClass }} alert-dismissible" role="alert"><strong>{{ alertPrefix }}</strong> {{ message }}</div></div>';
    return Mustache.render(template, {
        'message': message,
        'alertClass': alertClass,
        'alertPrefix': alertPrefix
    });
}

function error(message) {
    return notification('error', message)
}

function success(message) {
    return notification('success', message)
}

function deserialize(formId, obj) {
    $.each(obj, function(key, value) {
        if ($('#' + formId + ' :input[name=' + key + ']').prop('type') == 'radio')
            $('#' + formId + ' :input[name=' + key + '][type=radio][value=' + value + ']').prop('checked', 'true');
        else
            $('#' + formId + ' :input[name=' + key + '][type!=radio]').val(value);
    });
}

/* -------------
 * API Utilities
 * ------------- */

function getResource(href, params) {
    params = params || '';
    return $.ajax({
        type: 'GET',
        url: href,
        data: $.param(params),
        async: false
    });
}

function getCurrentUser(params) {
    params = params || '';
    return $.ajax({
        type: 'GET',
        url: '/api/auth/sign_in/',
        data: $.param(params),
        async: false
    });
}

// Potentially return other users later
function loadUser() {
    return globals.currentUser;
}

function getUsers(params) {
    params = params || '';
    return $.ajax({
        type: 'GET',
        url: '/api/users/',
        data: $.param(params)
    });
}

function userToUserPicture(user) {
    return $.ajax({
        type: 'GET',
        url: user.picture.href,
    });
}

function userToUserLounges(user, params) {
    params = params || '';
    return $.ajax({
        type: 'GET',
        url: user.userLounges.href,
        data: $.param(params) 
    });
}

function userToHostApplications(user) {
    return $.ajax({
        type: 'GET',
        url: user.hostApplications.href
    });
}

function getLounges(params) {
    params = params || '';
    return $.ajax({
        type: 'GET',
        url: '/api/lounges/',
        data: $.param(params) 
    });
}

function loungeToLoungeUsers(lounge, params) {
    params = params || '';
    return $.ajax({
        type: 'GET',
        url: lounge.loungeUsers.href,
        data: $.param(params) 
    });
}

function loungeToPictures(lounge) {
    return $.ajax({
        type: 'GET',
        url: lounge.pictures.href,
    });
}

function loungeUserToUser(loungeUser) {
    return $.ajax({
        type: 'GET',
        url: loungeUser.user.href
    });
}

function userLoungeToLounge(userLounge) {
    return $.ajax({
        type: 'GET',
        url: userLounge.lounge.href
    });
}

function loungeToHost(lounge) {
    var hostLoungeUserPromise = loungeToLoungeUsers(lounge, {type: 'host'})
    return hostLoungeUserPromise.then(function(loungeUsers, textStatus, jqXHR) {
        var hostLoungeUser = loungeUsers.items[0];
        return loungeUserToUser(hostLoungeUser);
    });
}

function loungeToPictures(lounge) {
    return $.ajax({
        type: 'GET',
        url: lounge.pictures.href
    });
}

function getAuthentication(user) {
    var authentication;
    $.ajax({
        type: 'GET',
        url: user.key.href,
        async: false
    }).done(function(key, textStatus, jqXHR) {
        authentication = {
            'Authorization-API-Key': key.key
        }
    }).fail(function(key, textStatus, jqXHR) {
        keyString = null;
    });
    return authentication;
}
