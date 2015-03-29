"use strict";

$(document).ready(function() {
    loadAccounts();
});

function getUserData(user) {
    return userToHostApplications(user).then(function(hostApplications, textStatus, jqXHR) {
        var userData = JSON.parse(JSON.stringify(user));
        userData.hostApplications = hostApplications;
        return userData;
    });
}

function loadAccounts() {
    function loadAccountsError() {
        $('#accounts-error').html(error('We couldn\'t load accounts. Please refresh the page to try again.'));
        return;
    }

    getUsers().done(function(accounts) {
        var template = $('#accounts-template').html();
        var rendered = Mustache.render(template, accounts);
        $('#accounts').html(rendered);
    }).fail(function(error, textStatus, jqXHR) {
        loadAccountsError();
    });
}

$('.host-btn').click(function(event) {
    event.preventDefault();

    function denyhostapplicationerror() {
        $('#potential-hosts').html(error('we couldn\'t deny this host application. please refresh the page to try again.'));
        return;
    }

    var hostapplicationhref = $(event.target).closest('.host-application').attr('data-host-application-href')

    $.get(hostapplicationhref).then(function(hostapplication, textstatus, jqxhr) {
        hostapplication.isapproved = false;
        $.ajax({
            type: 'put',
            url: hostapplication.href,
            data: json.stringify(hostapplication),
            contenttype: 'application/json',
            headers: getauthentication(loaduser())
        }).then(function(hostapplication, textstatus, jqxhr) {
            loadhostapplications();
        }).fail(function(error, textstatus, jqxhr) {
            denyhostapplicationerror();
        })
    });
});

$('#accounts').on('click', '.admin-btn', function(event) {
    event.preventDefault();
    var userHref = $(event.target).closest('li').attr('data-user-href');
    updateRole(userHref, 'admin');
});

$('#accounts').on('click', '.host-btn', function(event) {
    event.preventDefault();
    var userHref = $(event.target).closest('li').attr('data-user-href');
    updateRole(userHref, 'host');
});

$('#accounts').on('click', '.lounger-btn', function(event) {
    event.preventDefault();
    var userHref = $(event.target).closest('li').attr('data-user-href');
    updateRole(userHref, 'lounger');
});

function updateRole(userHref, role) {
    function updateRoleError() {
        $('#accounts-error').html(error('We couldn\'t update this user\'s role. Please refresh the page to try again.'));
        return;
    }

    $.get(userHref).then(function(user, textStatus, jqXHR) {
        user.role = role;
        $.ajax({
            type: 'PUT',
            url: userHref,
            data: JSON.stringify(user),
            contentType: 'application/json',
            headers: getAuthentication(globals.currentUser)
        }).then(function(user, textStatus, jqXHR) {
            loadAccounts();          
        }).fail(function(error, textStatus, jqXHR) {
            updateRoleError();           
        });
    });
    console.log(user.role);
}
