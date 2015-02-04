"use strict";

$(document).ready(function() {
    loadHostedLounges();
});

function getUserLoungeData(userLounge) {
    return $.when(userLoungeToLounge(userLounge)).then(function(lounge, textStatus, jqXHR) {
        var userLoungeData = JSON.parse(JSON.stringify(userLounge));
        userLoungeData.lounge = lounge;
        userLoungeData.lounge.dateTime = formatDateTime(userLoungeData.lounge.dateTime); 
        return userLoungeData;
    });
}

function loadHostedLounges() {
    var user = loadUser();

    function loadHostedLoungesError() {
        $('#welcomeMessage').html(error('We couldn\'t load your hosted lounges. Please refresh the page to try again.'));
        return;
    }

    var hostedUserLoungesPromise = userToUserLounges(user, {type: 'host'});

    hostedUserLoungesPromise.then(function(hostedUserLounges, textStatus, jqXHR) {
        var hostedUserLoungesDataPromises = hostedUserLounges.items.map(function(hostedUserLounge) {
            return getUserLoungeData(hostedUserLounge);
        });

        return $.when.apply($, hostedUserLoungesDataPromises).then(function() {
            return {
                'items': getArguments(arguments)
            };
        });
    }).done(function(hostedUserLoungesData) {
        var template = $('#hostedLoungesTemplate').html();
        var rendered = Mustache.render(template, hostedUserLoungesData);
        $('#hostedLounges').html(rendered);
    }).fail(function(error, textStatus, jqXHR) {
        loadHostedLoungesError();
    });
}

$('#hostLoungeAnchor').click(function(event) {
    event.preventDefault();
    $('#hostLoungeModal').modal(); 
    $('#hostLoungeFormBtn').show()
});

function prepareFormLoungeData(formLoungeData) {
    var dateTime = moment(formLoungeData.date + 'T' + formLoungeData.time);
    formLoungeData.dateTime = dateTime.utc().format();

    if ('isReserved' in formLoungeData) {
        formLoungeData.isReserved = true;
    }
    else {
        formLoungeData.isReserved = false; 
    }
    return formLoungeData;
} 

$('#hostLoungeForm').submit(function(event) {
    function hostLoungeError() {
        $('#hostLoungeError').html(error('We couldn\'t create a lounge for you to host. Please refresh the page to try again.'));
        return;
    }
    
    function hostLoungeBadRequestError() {
        // Theoretically not possible via UI
        $('#hostLoungeError').html(error('There are some errors with your input (possibly the date or time). Please fix them and try again.'));
        return;
    }
    
    function hostLoungeSuccess() {
        $('#hostLoungeError').html(success('You\'re going to host a lounge. Good luck!'));
        return;
    }

    event.preventDefault();
    var formLoungeData = $('#hostLoungeForm').serializeObject();
    var loungeData = prepareFormLoungeData(formLoungeData); 

    $.ajax({
        type: 'POST',
        url: '/api/lounges/',
        data: JSON.stringify(loungeData),
        contentType: 'application/json',
        headers: getAuthentication(loadUser())
    }).done(function(lounge, textStatus, jqXHR) {
        hostLoungeSuccess();
        $('#hostLoungeFormBtn').hide();
        loadHostedLounges();
        loadUpcomingUserLounges();
    }).fail(function(error, textStatus, jqXHR) {
        if (error.status == 400) {
            hostLoungeBadRequestError();
        }
        else {
            hostLoungeError();
        }
    });
})

$('#hostedLounges').on('click', '.hostedLounge', function(event) {
    function logLoungeLoadError() {
        $('#logLoungeError').html(error('We couldn\'t load this lounge for you to log. Please refresh the page to try again.'));
        return;
    }
    event.preventDefault();
    $('#logLoungeModal').modal();
    
    var loungeHref = $(event.target).closest('a').prop('id');

    var loungePromise = $.get(loungeHref)
    loungePromise.then(function(lounge, textStatus, jqXHR) {
        loungeToLoungeUsers(lounge, {expand: 'user'}).then(function(loungeUsers, textStatus, jqXHR) {
            loungeToPictures(lounge).then(function(pictures, textStatus, jqXHR) {
                $.each(loungeUsers.items, function(index, loungeUser) {
                    loungeUser.showedUpChecked = loungeUser.showedUp ? 'checked' : '';
                    loungeUser.hostedClass = loungeUser.isHost ? 'host' : '';
                });
                lounge.loungeUsers = loungeUsers;
                lounge.pictures = pictures;
                lounge.date = formatISODate(lounge.dateTime)
                lounge.time = formatISOTime(lounge.dateTime)
                lounge.reservedChecked = lounge.isReserved ? 'checked' : '';
                var template = $('#logUserLoungesTemplate').html();
                var rendered = Mustache.render(template, lounge);
                $('#logUserLoungesModalContent').html(rendered);
            })
        }).fail(function(error, textStatus, jqXHR) {
            logLoungeLoadError();
        });
    });
});

function prepareFormUserLoungeData(formUserLoungeData) {
    if ('showedUp' in formUserLoungeData) {
        formUserLoungeData.showedUp = true;
    }
    else {
        formUserLoungeData.showedUp = false; 
    }
    return formUserLoungeData;
} 

// Can just do logLoungeForm.submit since not being loaded dynamically, after moving templating inside the form
$('#logLoungeModal').on('submit', '#logLoungeForm', function(event) {
    event.preventDefault();
   
    var loungeHref = $('.logLounge').attr('data-log-lounge-href')
    
    if (globals.logLoungeAction == 'submit') {
        var formLogLoungeData = $('.logLounge :input').serializeObject();
        var logLoungeData = prepareFormLoungeData(formLogLoungeData);
        logLounge(loungeHref, logLoungeData);
    }
    else if (confirm('Are you sure you want to delete this lounge? This cannot be undone.')) {
        deleteLounge(loungeHref)
    }
});

function logLounge(loungeHref, logLoungeData) {
    function logLoungeError() {
        $('#logLoungeError').html(error('We couldn\'t log your lounge. Please refresh the page to try again.'));
        return;
    }
    
    function logLoungeSuccess() {
        $('#logLoungeError').html(success('You logged your lounge.'));
        return;
    }

    var logLoungePromise = $.ajax({
        type: 'PUT',
        url: loungeHref,
        data: JSON.stringify(logLoungeData),
        contentType: 'application/json',
        headers: getAuthentication(globals.currentUser) 
    })

    var logPromises = [logLoungePromise];

    $('.logLoungeUser').each(function(index, logLoungeUser) {
        logLoungeUser = $(logLoungeUser);
        var loungeUserHref = logLoungeUser.attr('data-log-lounge-user-href');
        var userHref = logLoungeUser.attr('data-log-user-href');
        
        var formLogLoungeUserData = $(logLoungeUser).find(':input, textarea').serializeObject();
        var logLoungeUserData = prepareFormUserLoungeData(formLogLoungeUserData);
        
        logLoungeUserData.user = {
            'href': userHref
        };
        if (logLoungeUser.hasClass('host')) {
            logLoungeUserData.isHost = true;
        }
        else {
            logLoungeUserData.isHost = false;
        }

        logPromises.push($.ajax({
            type: 'PUT',
            url: loungeUserHref,
            data: JSON.stringify(logLoungeUserData),
            contentType: 'application/json',
            headers: getAuthentication(globals.currentUser) 
        }));
    });

    var loungePicturesHref;
    $.get(loungeHref).then(function(lounge, textStatus, jqXHR) {
        loungePicturesHref = lounge.pictures.href;
    }).then(function() {
        var pictureUploadPromises = [];
        var files = $('#upload-lounge-pictures-files')[0].files;
        for (var i = 0; i < files.length; i++) {
            var formData = new FormData();
            formData.append("file", files[i]) 
            
            pictureUploadPromises.push($.ajax({
                type: 'POST',
                url: '/api/pictures/',
                data: formData,
                contentType: false,
                cache: false,
                processData: false
            }).then(function(picture, textStatus, jqXHR) {
                console.log(loungePicturesHref)
                return $.ajax({
                    type: 'POST',
                    url: loungePicturesHref,
                    data: JSON.stringify({'picture': picture}),
                    contentType: 'application/json',
                    headers: getAuthentication(loadUser())
                });
            }));
        }

        $.when.apply($, logPromises.concat(pictureUploadPromises)).done(function() {
            logLoungeSuccess();
        }).fail(function() {
            logLoungeError();
        });
    });
}

function deleteLounge(loungeHref) {
    function deleteLoungeError() {
        $('#logLoungeError').html(error('We couldn\'t delete this lounge. Please refresh the page to try again.'));
        return;
    }
        
    $.ajax({
        type: 'DELETE',
        url: loungeHref,
        headers: getAuthentication(globals.currentUser)
    }).done(function(_, textStatus, jqXHR) {
        location.reload();
    }).fail(function(error, textStatus, jqXHR) {
        deleteLoungeError();
    });
}

$('#logLoungeModal').on('click', '.delete-picture-btn', function(event) {
    function deleteLoungePictureError() {
        $('#lounge-picture-error').html(error('We couldn\'t delete this picture. Please refresh the page to try again.'));
        return;
    }
    
    function deleteLoungePictureSuccess() {
        $('#lounge-picture-error').html(success('This picture is deleted. Refresh to update pictures.'));
        return;
    }

    event.preventDefault();
 
    var loungePictureHref = $(event.target).closest('div').attr('data-lounge-picture-href');
    
    $.ajax({
        type: 'DELETE',
        url: loungePictureHref,
        headers: getAuthentication(globals.currentUser)
    }).done(function(_, textStatus, jqXHR) {
        deleteLoungePictureSuccess();
    }).fail(function(_, textStatus, jqXHR) {
        deleteLoungePictureError();
    });
});
