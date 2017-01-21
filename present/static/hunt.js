$(function () {
  $('[data-toggle="tooltip"]').tooltip({
    template: '<div class="tooltip"><div class="tooltip-inner"></div></div>'
  });

  var answerHashCodes = {};
  $.getJSON("/static/answer_hash_codes.json", function(data) {
    answerHashCodes = data;
  });

  $("#checkAnswerTextbox").on("change keyup paste", function(event) {
    var answerHashCode = answerHashCodes[puzzleId];
    if (answerHashCode === undefined) {
      $("#checkAnswerTextbox").css("background-color", "white");
      return;
    }

    var submission = $("#checkAnswerTextbox").val();
    if (!submission) {
      $("#checkAnswerTextbox").css("background-color", "white");
      return;
    }

    var strippedSubmission = submission.toUpperCase().replace(/[^A-Z0-9]/g, "");
    var submissionHashCode = 0;
    for (var i = 0; i < strippedSubmission.length; i++) {
      var char = strippedSubmission.charCodeAt(i);
      submissionHashCode = ((submissionHashCode << 5) - submissionHashCode) + char;
      submissionHashCode = submissionHashCode & submissionHashCode;
    }

    if (submissionHashCode == answerHashCode) {
      $("#checkAnswerTextbox").css("background-color", "#80ff80");
    } else {
      $("#checkAnswerTextbox").css("background-color", "#ff8080");
    }
  });
})
