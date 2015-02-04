"use strict";

$(document).ready(function() {
    loadLounges();
    loadHosts();
    loadLogLounges();
});

// Creates a copy of lounge and assocs in a formatted DateTime, remaining spots, and the lounge's host
function getLoungeData(lounge) {
    return $.when(loungeToLoungeUsers(lounge), loungeToHost(lounge)).then(function(loungeUsersData, hostData) {
        var loungeUsers = loungeUsersData[0]
        var host = hostData[0]
        
        var loungeData = JSON.parse(JSON.stringify(lounge));
        loungeData.dateTime = formatDateTime(loungeData.dateTime);
        
        // 6 isn't a server-side hardcap, just client-side 
        loungeData.left = Math.max(6 - loungeUsers.items.length, 0);
        loungeData.leftPlurality = loungeData.left == 1 ? 'spot' : 'spots';

        loungeData.host = host;
        return loungeData;
    });
}

function loadLounges() {
    function loadLoungesError() {
        $('#lounges').html(error('We couldn\'t load the upcoming lounges. Please refresh the page to try again.'));
        return;
    }

    var loungesPromise = getLounges({time: 'future', limit: 5})
        
    loungesPromise = loungesPromise.then(function(lounges, textStatus, jqXHR) {
        var loungesDataPromises = lounges.items.map(function(lounge) {
            return getLoungeData(lounge);
        });
        return $.when.apply($, loungesDataPromises).then(function() {
            return {
                'items': getArguments(arguments)
            };
        });
    });
        
    loungesPromise.done(function(lounges) {
        var template = $('#loungesTemplate').html();
        var rendered = Mustache.render(template, lounges); 
        $('#lounges').html(rendered);
        globals.lounges = lounges;
    }).fail(function(error, textStatus, jqXHR) {
        loadLoungesError();
    });
}
        
$('#lounges').on('click', '.lounge', function(event) {
    event.preventDefault();
        
    // Handle a user trying to sign up for a lounge before signing in/up
    if (!globals.currentUser) {
        $('#register-error').html(error('You need to sign in before registering for a lounge. You can sign in or sign up at the top right.'));
        return;
    }

    $('#loungeRegisterModal').modal()
   
    // Button is hidden when a user submits; reshow for another lounge 
    $('#loungeRegisterFormBtn').show();

    var loungeHref = $(event.target).closest('a').prop('id');
    var lounges = globals.lounges;
    var lounge = lounges.items.filter(function(lounge) {
        return lounge.href == loungeHref;
    })[0];
    globals.loungeToRegister = lounge;
     
    var template = $('#loungeRegisterTemplate').html();
    var rendered = Mustache.render(template, lounge);
    $('#loungeRegister').html(rendered);
})

$('#loungeRegisterForm').submit(function(event) {
    function loungeRegisterError() {
        $('#loungeRegister').html(error('We couldn\'t register you for this lounge. Please refresh the page to try again.'));
        return;
    }
    
    function loungeRegisterConflictError() {
        $('#loungeRegister').html(error('You\'re already signed up for this lounge. See you there!'));
        return;
    }
    
    function loungeRegisterSuccess() {
        $('#loungeRegister').html(success('Congratulations, you\'re signed up for this lounge. See you there!'));
        return;
    }

    event.preventDefault();
    
    var lounge = {
        isHost: false,
        lounge: {
            href: globals.loungeToRegister.href 
        }
    }

    $.ajax({
        type: 'POST',
        url: globals.currentUser.userLounges.href,
        data: JSON.stringify(lounge),
        headers: getAuthentication(globals.currentUser),
        contentType: 'application/json'
    }).done(function(lounges, textStatus, jqXHR) {
        loungeRegisterSuccess();
        $('#loungeRegisterFormBtn').hide();
    }).fail(function(error, textStatus, jqXHR) {
        if (error.status == 409) {
            loungeRegisterConflictError();
        }
        else {
            loungeRegisterError();
        }
    });
})


//MiniLog
function getLogLoungeData(logLounge) {
    return $.when(loungeToLoungeUsers(logLounge, {type: 'showed-up', expand: 'user'})).then(function(logLoungeUsersData) {
        var logLoungeUsers = logLoungeUsersData;
        var logLoungeData = JSON.parse(JSON.stringify(logLounge));
        logLoungeData.logLoungeUsers = logLoungeUsers;
        logLoungeData.logLoungeUsers['items'][ logLoungeData.logLoungeUsers['items'].length - 1 ].last = true;
        return logLoungeData;
    });
}

function loadLogLounges() {
    function loadLogLoungesError() {
        $('#logLounges').html(error('We couldn\'t load the previous lounges. Please refresh the page to try again.'));
        return;
    }

    var logLoungesPromise = getLounges({time: 'past', limit: 3})

    logLoungesPromise = logLoungesPromise.then(function(logLounges, textStatus, jqXHR) {
        var logLoungesDataPromises = logLounges.items.map(function(logLounge) {
            return getLogLoungeData(logLounge);
        });
        return $.when.apply($, logLoungesDataPromises).then(function() {
            return {
                'items': getArguments(arguments)
            };
        });
    });
        
    logLoungesPromise.done(function(logLounges) {
        var template = $('#logLoungesTemplate').html();
        var rendered = Mustache.render(template, logLounges); 
        $('#logLounges').html(rendered);
    }).fail(function(error, textStatus, jqXHR) {
        loadLogLoungesError();
    });
}

//Hosts
function getHostData(host) {
    return $.when(userToUserPicture(host)).then(function(hostPictureData) {
        var hostPicture = hostPictureData.image;
        var hostData = JSON.parse(JSON.stringify(host));
        hostData.picture = hostPicture;
        //hostData.firstName
        return hostData;
    });
}

function loadHosts() {
    function loadHostsError() {
        $('#hosts').html(error('We couldn\'t load our host profiles. Please refresh the page to try again.'));
        return;
    }

    var hostsPromise = getUsers({role: 'host,admin', limit: 6, sort: 'random'})

    hostsPromise = hostsPromise.then(function(hosts, textStatus, jqXHR) {
        var hostsDataPromises = hosts.items.map(function(host) {
            return getHostData(host);
        });

        return $.when.apply($, hostsDataPromises).then(function() {
            return {
                'items':getArguments(arguments)
            };
        });
    });

    hostsPromise.done(function(hosts) {
        var template = $('#hostsTemplate').html();
        console.log()
        var rendered = Mustache.render(template, hosts);
        $('#hosts').html(rendered);
    }).fail(function(error, textStatus, jqXHR) {
        loadHostsError();
    });
}
