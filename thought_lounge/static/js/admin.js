"use strict";

$(document).ready(function() {
    loadHostApplications();
});

function getUserData(user) {
    return userToHostApplications(user).then(function(hostApplications, textStatus, jqXHR) {
        var userData = JSON.parse(JSON.stringify(user));
        $.each(hostApplications.items, function(index, hostApplication) {
            hostApplication.application = hostApplication.application.split('\n');
        });
        userData.hostApplications = hostApplications;
        return userData;
    });
}

function loadHostApplications() {
    function loadHostApplicationsError() {
        $('#potential-hosts').html(error('We couldn\'t load the host applications. Please refresh the page to try again.'));
        return;
    }

    getUsers({role: 'lounger', require: 'host-applications'}).then(function(users, textStatus, jqXHR) {
        var userDataPromises = users.items.map(function(user) {
            return getUserData(user);
        })

        return $.when.apply($, userDataPromises).then(function() {
            return {
                'href': users.href, 
                'items': getArguments(arguments)
            };
        });
    }).done(function(usersData) {
        var template = $('#potential-hosts-template').html();
        var rendered = Mustache.render(template, usersData);
        $('#potential-hosts').html(rendered);
    }).fail(function(error, textStatus, jqXHR) {
        loadHostApplicationsError();
    });
}

$('#potential-hosts').on('click', '.potential-host-approve-btn', function(event) {
    event.preventDefault();

    function approveHostApplicationError() {
        $('#potential-hosts').html(error('We couldn\'t approve this host application. Please refresh the page to try again.'));
        return;
    }

    var hostApplicationHref = $(event.target).closest('.host-application').attr('data-host-application-href')

    $.get(hostApplicationHref).then(function(hostApplication, textStatus, jqXHR) {
        hostApplication.isApproved = true;
        $.ajax({
            type: 'PUT',
            url: hostApplication.href,
            data: JSON.stringify(hostApplication),
            contentType: 'application/json',
            headers: getAuthentication(loadUser())
        }).then(function(hostApplication, textStatus, jqXHR) {
            loadHostApplications();
        }).fail(function(error, textStatus, jqXHR) {
            approveHostApplicationError();
        })
    });
});

$('#potential-hosts').on('click', '.potential-host-deny-btn', function(event) {
    event.preventDefault();

    function denyHostApplicationError() {
        $('#potential-hosts').html(error('We couldn\'t deny this host application. Please refresh the page to try again.'));
        return;
    }

    var hostApplicationHref = $(event.target).closest('.host-application').attr('data-host-application-href')

    $.get(hostApplicationHref).then(function(hostApplication, textStatus, jqXHR) {
        hostApplication.isApproved = false;
        $.ajax({
            type: 'put',
            url: hostApplication.href,
            data: JSON.stringify(hostApplication),
            contentType: 'application/json',
            headers: getAuthentication(loadUser())
        }).then(function(hostApplication, textStatus, jqXHR) {
            loadHostApplications();
        }).fail(function(error, textStatus, jqXHR) {
            denyHostApplicationError();
        });
    });
});
