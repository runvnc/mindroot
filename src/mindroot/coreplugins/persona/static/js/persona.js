window.registerCommandHandler('pic_of_me', (data) => {
    console.log('pic_of_me', data);
    if (data.event == 'partial') {
      console.log('partial')
      return '<div class="spinner">&nbsp;</div>'
    } else {
      console.log('not partial')
      return ''
    }
});
